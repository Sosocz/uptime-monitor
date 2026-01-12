import { createClient } from '@supabase/supabase-js';
import { Client } from 'pg';
import crypto from 'crypto';

const sourceDbUrl = process.env.SOURCE_DATABASE_URL || process.env.DATABASE_URL || '';
const supabaseDbUrl = process.env.SUPABASE_DB_URL || '';
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL || '';
const supabaseServiceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY || '';

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
  const { rows } = await source.query(`select * from ${table}`);
  if (!rows.length) return;

  const columns = Object.keys(rows[0]);
  const columnList = columns.map((c) => `"${c}"`).join(', ');

  for (const row of rows) {
    const data = columnOverride ? columnOverride(row) : row;
    const values = columns.map((c) => data[c]);
    const params = values.map((_, idx) => `$${idx + 1}`).join(', ');
    await target.query(
      `insert into public.${table} (${columnList}) values (${params}) on conflict do nothing`,
      values
    );
  }
}

async function main() {
  await source.connect();
  await target.connect();

  const userPasswordMap: Record<string, string> = {};

  await copyTable('users', (row) => {
    const email = row.email as string;
    if (!row.auth_user_id) {
      // Create auth user and map
      // eslint-disable-next-line @typescript-eslint/no-floating-promises
      // handled sequentially below
    }
    return row;
  });

  const { rows: users } = await source.query('select * from users');
  for (const user of users) {
    if (!user.auth_user_id) {
      const { authUserId, tempPassword } = await createAuthUser(user.email);
      user.auth_user_id = authUserId;
      userPasswordMap[user.email] = tempPassword;
    }

    await target.query(
      `insert into public.users (id, auth_user_id, email, plan, stripe_customer_id, stripe_subscription_id, telegram_chat_id, webhook_url, is_active, created_at, updated_at, first_name, last_name, phone, timezone, avatar_url, alerts_enabled, alerts_paused_from, alerts_paused_until, oauth_provider, oauth_id, password_reset_token, password_reset_expires_at, onboarding_completed, onboarding_email_j1_sent, onboarding_email_j3_sent)
       values ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,now(),$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22,$23,$24,$25)
       on conflict (id) do nothing`,
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

  for (const table of TABLE_ORDER) {
    if (table === 'users') continue;
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

  for (const seq of sequences) {
    const table = seq.replace('_id_seq', '');
    await target.query(`select setval('public.${seq}', (select coalesce(max(id), 1) from public.${table}));`);
  }

  console.log('Migration complete. Temp passwords for created auth users:', userPasswordMap);

  await source.end();
  await target.end();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
