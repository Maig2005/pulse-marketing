(function() {

  const API = "https://pulse-marketing.onrender.com";

  // ----------------------------
  // SESSION ID
  // ----------------------------
  function getSessionId() {
    let sessionId = localStorage.getItem("session_id");
    if (!sessionId) {
      sessionId = "sess_" + Math.random().toString(36).substr(2, 9);
      localStorage.setItem("session_id", sessionId);
    }
    return sessionId;
  }

  // ----------------------------
  // SEND EVENT
  // ----------------------------
  function sendEvent(eventType) {
    fetch(API + "/track", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event_type: eventType,
        page: window.location.href, // ✅ FIXED
        timestamp: new Date().toISOString(), // ✅ FIXED
        session_id: getSessionId() // ✅ FIXED
      })
    })
    .then(res => res.json())
    .then(data => console.log("TRACK:", data))
    .catch((e) => console.error("TRACK ERROR:", e)); // ✅ SHOW ERRORS
  }

  // ----------------------------
  // DECISION FETCH
  // ----------------------------
  function getDecision() {
    const sessionId = getSessionId();

    fetch(API + "/decision/" + sessionId)
      .then(res => res.json())
      .then(data => {
        console.log("DECISION:", data); // DEBUG

        if (data.action === "show_offer") {
          showOffer(data.message);
        } else if (data.action === "show_chatbot") {
          showChatbot();
        }
      })
      .catch((e) => console.error("DECISION ERROR:", e));
  }

  // ----------------------------
  // UI ACTIONS
  // ----------------------------
  function showOffer(message) {
    const old = document.getElementById("ai-offer-banner");
    if (old) old.remove();

    const banner = document.createElement("div");
    banner.id = "ai-offer-banner";

    banner.innerHTML = `
      <div style="position:fixed;bottom:20px;right:20px;background:#fff;padding:15px;border-radius:10px;box-shadow:0 0 10px rgba(0,0,0,0.2);z-index:9999;">
        <div><b>🔥 Special Offer</b></div>
        <div>${message}</div>
        <button onclick="handleCTA()" style="margin-top:10px;">Claim Offer</button>
      </div>
    `;

    document.body.appendChild(banner);
  }

  function showChatbot() {
    alert("Need help? Chat with us!");
  }

  // ----------------------------
  // MAIN ENTRY POINT
  // ----------------------------
  window.addEventListener("load", () => {
    sendEvent("page_view");
    setTimeout(getDecision, 1000);
  });

  // ----------------------------
  // CLICK TRACKING
  // ----------------------------
  document.addEventListener("click", () => {
    sendEvent("click");
  });

})();

// ----------------------------
// CTA HANDLER (GLOBAL)
// ----------------------------
function handleCTA() {

  const sessionId = localStorage.getItem("session_id"); // ✅ FIX

  fetch("https://pulse-marketing.onrender.com/track", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      event_type: "click",
      page: window.location.href, // ✅ FIXED
      timestamp: new Date().toISOString(), // ✅ FIXED
      session_id: sessionId // ✅ FIXED
    })
  })
  .then(res => res.json())
  .then(data => console.log("CTA TRACK:", data))
  .catch(err => console.error("CTA ERROR:", err));

  alert("Redirecting to your offer...");
  setTimeout(() => { window.location.href = "https://amazon.com"; }, 1000);
}