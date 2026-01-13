import { createClient } from '@supabase/supabase-js';
import { Client } from 'pg';
import crypto from 'crypto';
import fs from 'fs';

const sourceDbUrl = process.env.SOURCE_DATABASE_URL || process.env.DATABASE_URL || '';
const supabaseDbUrl = process.env.SUPABASE_DB_URL || '';
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL || '';
const supabaseServiceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY || '';
const args = process.argv.slice(2);
const dryRun = args.includes('--dry-run');
const tablesArg = args.find((arg) => arg.startsWith('--tables='));
const limitArg = args.find((arg) => arg.startsWith('--limit='));
const batchArg = args.find((arg) => arg.startsWith('--batch-size='));
const logFileArg = args.find((arg) => arg.startsWith('--log-file='));
const limit = limitArg ? Number(limitArg.split('=')[1]) : 0;
const batchSize = batchArg ? Number(batchArg.split('=')[1]) : 500;
const logFile = logFileArg ? logFileArg.split('=')[1] : '';

function log(message: string) {
  const line = `[${new Date().toISOString()}] ${message}`;
  console.log(line);
  if (logFile) {
    fs.appendFileSync(logFile, line + '\n');
  }
}

if (!sourceDbUrl || !supabaseDbUrl || !supabaseUrl || !supabaseServiceRoleKey) {
  console.error('Missing env. Required: SOURCE_DATABASE_URL, SUPABASE_DB_URL, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseServiceRoleKey, {
  auth: { persistSession: false, autoRefreshToken: false }
});

const source = new Client({ connectionString: sourceDbUrl });
const target = new Client({ connectionString: supabaseDbUrl });

const TABLE_ORDER = [
  'users',
  'monitors',
  'checks',
  'escalation_rules',
  'incidents',
  'incident_roles',
  'notification_logs',
  'status_pages',
  'status_page_monitors',
  'status_page_subscribers',
  'subscriptions',
  'usage_records',
  'oncall_schedules',
  'oncall_shifts',
  'cover_requests',
  'services',
  'webhooks',
  'webhook_logs',
  'error_projects',
  'error_groups',
  'error_events'
];

async function createAuthUser(email: string) {
  const tempPassword = crypto.randomBytes(12).toString('hex');
  const { data, error } = await supabase.auth.admin.createUser({
    email,
    password: tempPassword,
    email_confirm: true
  });
  if (error || !data.user) {
    throw new Error(`Failed to create auth user for ${email}: ${error?.message}`);
  }
  return { authUserId: data.user.id, tempPassword };
}

async function copyTable(table: string, columnOverride?: (row: any) => any) {
  const countResult = await source.query(`select count(*) as count from ${table}`);
  const total = Number(countResult.rows[0]?.count || 0);
  if (!total) {
    log(`Table ${table}: 0 rows`);
    return;
  }

  const limitTotal = limit && limit < total ? limit : total;
  log(`Table ${table}: migrating ${limitTotal} rows`);

  for (let offset = 0; offset < limitTotal; offset += batchSize) {
    const batchLimit = Math.min(batchSize, limitTotal - offset);
    const { rows } = await source.query(
      `select * from ${table} order by id asc limit $1 offset $2`,
      [batchLimit, offset]
    );
    if (!rows.length) break;

    const columns = Object.keys(rows[0]);
    const columnList = columns.map((c) => `"${c}"`).join(', ');
    const updateList = columns
      .filter((c) => c !== 'id')
      .map((c) => `"${c}" = excluded."${c}"`)
      .join(', ');

    for (const row of rows) {
      const data = columnOverride ? columnOverride(row) : row;
      const values = columns.map((c) => data[c]);
      const params = values.map((_, idx) => `$${idx + 1}`).join(', ');
      if (dryRun) {
        continue;
      }
      await target.query(
        `insert into public.${table} (${columnList}) values (${params}) on conflict (id) do update set ${updateList}`,
        values
      );
    }
  }
}

async function main() {
  await source.connect();
  await target.connect();

  const userPasswordMap: Record<string, string> = {};

  const { rows: users } = await source.query('select * from users');
  for (const user of users) {
    if (!user.auth_user_id) {
      if (dryRun) {
        log(`Dry-run: would create Supabase auth user for ${user.email}`);
      } else {
        const { authUserId, tempPassword } = await createAuthUser(user.email);
        user.auth_user_id = authUserId;
        userPasswordMap[user.email] = tempPassword;
      }
    }

    if (!dryRun) {
      await target.query(
        `insert into public.users (id, auth_user_id, email, plan, stripe_customer_id, stripe_subscription_id, telegram_chat_id, webhook_url, is_active, created_at, updated_at, first_name, last_name, phone, timezone, avatar_url, alerts_enabled, alerts_paused_from, alerts_paused_until, oauth_provider, oauth_id, password_reset_token, password_reset_expires_at, onboarding_completed, onboarding_email_j1_sent, onboarding_email_j3_sent)
         values ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,now(),$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22,$23,$24,$25)
         on conflict (id) do update set auth_user_id = excluded.auth_user_id, email = excluded.email, plan = excluded.plan, stripe_customer_id = excluded.stripe_customer_id, stripe_subscription_id = excluded.stripe_subscription_id, telegram_chat_id = excluded.telegram_chat_id, webhook_url = excluded.webhook_url, is_active = excluded.is_active, updated_at = now(), first_name = excluded.first_name, last_name = excluded.last_name, phone = excluded.phone, timezone = excluded.timezone, avatar_url = excluded.avatar_url, alerts_enabled = excluded.alerts_enabled, alerts_paused_from = excluded.alerts_paused_from, alerts_paused_until = excluded.alerts_paused_until, oauth_provider = excluded.oauth_provider, oauth_id = excluded.oauth_id, password_reset_token = excluded.password_reset_token, password_reset_expires_at = excluded.password_reset_expires_at, onboarding_completed = excluded.onboarding_completed, onboarding_email_j1_sent = excluded.onboarding_email_j1_sent, onboarding_email_j3_sent = excluded.onboarding_email_j3_sent`,
        [
          user.id,
          user.auth_user_id,
          user.email,
          user.plan,
          user.stripe_customer_id,
          user.stripe_subscription_id,
          user.telegram_chat_id,
          user.webhook_url,
          user.is_active,
          user.created_at,
          user.first_name,
          user.last_name,
          user.phone,
          user.timezone,
          user.avatar_url,
          user.alerts_enabled,
          user.alerts_paused_from,
          user.alerts_paused_until,
          user.oauth_provider,
          user.oauth_id,
          user.password_reset_token,
          user.password_reset_expires_at,
          user.onboarding_completed,
          user.onboarding_email_j1_sent,
          user.onboarding_email_j3_sent
        ]
      );
    }
  }

  const selectedTables = tablesArg
    ? tablesArg.split('=')[1].split(',').map((t) => t.trim()).filter(Boolean)
    : TABLE_ORDER;

  for (const table of TABLE_ORDER) {
    if (table === 'users') continue;
    if (selectedTables.length && !selectedTables.includes(table)) continue;
    await copyTable(table);
  }

  const sequences = [
    'users_id_seq',
    'monitors_id_seq',
    'checks_id_seq',
    'escalation_rules_id_seq',
    'incidents_id_seq',
    'incident_roles_id_seq',
    'notification_logs_id_seq',
    'status_pages_id_seq',
    'status_page_monitors_id_seq',
    'status_page_subscribers_id_seq',
    'subscriptions_id_seq',
    'usage_records_id_seq',
    'oncall_schedules_id_seq',
    'oncall_shifts_id_seq',
    'cover_requests_id_seq',
    'services_id_seq',
    'webhooks_id_seq',
    'webhook_logs_id_seq',
    'error_projects_id_seq',
    'error_groups_id_seq',
    'error_events_id_seq'
  ];

  if (!dryRun) {
    for (const seq of sequences) {
      const table = seq.replace('_id_seq', '');
      await target.query(`select setval('public.${seq}', (select coalesce(max(id), 1) from public.${table}));`);
    }
  }

  log('Migration complete.');
  if (Object.keys(userPasswordMap).length) {
    log(`Temp passwords for created auth users: ${JSON.stringify(userPasswordMap, null, 2)}`);
  }

  await source.end();
  await target.end();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
