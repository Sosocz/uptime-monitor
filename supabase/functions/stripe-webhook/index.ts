import "https://deno.land/x/dotenv/load.ts";
import Stripe from "https://esm.sh/stripe@13.10.0?target=deno";

const stripeSecretKey = Deno.env.get("STRIPE_SECRET_KEY") ?? "";
const webhookSecret = Deno.env.get("STRIPE_WEBHOOK_SECRET") ?? "";

const stripe = new Stripe(stripeSecretKey, {
  apiVersion: "2023-10-16",
});

Deno.serve(async (req) => {
  if (req.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }

  const signature = req.headers.get("stripe-signature") ?? "";
  const body = await req.text();

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(body, signature, webhookSecret);
  } catch (err) {
    return new Response(`Webhook error: ${err.message}`, { status: 400 });
  }

  // TODO: move Stripe handling logic here or forward to backend if needed.
  console.log(`Received Stripe event: ${event.type}`);

  return new Response("ok", { status: 200 });
});
