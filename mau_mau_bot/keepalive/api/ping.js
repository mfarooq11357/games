const HEALTH_PATH = "/health";

function healthUrl() {
  const configured = process.env.BOT_HEALTH_URL;
  if (configured) {
    return configured;
  }
  const base = process.env.BOT_URL;
  if (!base) {
    return "";
  }
  return base.replace(/\/$/, "") + HEALTH_PATH;
}

module.exports = async function handler(req, res) {
  const secret = process.env.CRON_SECRET;
  if (secret) {
    const auth = req.headers.authorization || "";
    if (auth !== `Bearer ${secret}`) {
      res.status(401).json({ ok: false, error: "unauthorized" });
      return;
    }
  }

  const url = healthUrl();
  if (!url) {
    res.status(500).json({
      ok: false,
      error: "Set BOT_HEALTH_URL to the Render /health address",
    });
    return;
  }

  try {
    const response = await fetch(url, { cache: "no-store" });
    const body = await response.text();
    res.status(200).json({
      ok: response.ok,
      status: response.status,
      pinged: url,
      body: body.slice(0, 300),
    });
  } catch (error) {
    res.status(502).json({ ok: false, pinged: url, error: String(error) });
  }
};
