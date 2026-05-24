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
  // SEND EVENT (fire-and-forget)
  // ----------------------------
  function sendEvent(eventType) {
    fetch(API + "/track", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event_type: eventType,
        timestamp: Date.now(),
        page: window.location.pathname,
        session_id: getSessionId()
      })
    }).catch(() => {}); // silently ignore failures
  }

  // ----------------------------
  // DECISION FETCH
  // ----------------------------
  function getDecision() {
    const sessionId = getSessionId();

    fetch("https://pulse-marketing.onrender.com/decision/" + sessionId)
      .then(res => {
        if (!res.ok) throw new Error("Non-OK response");
        return res.json();
      })
      .then(data => {
        if (data.action === "show_offer") {
          showOffer(data.message);
        } else if (data.action === "show_chatbot") {
          showChatbot();
        }
      })
      .catch(() => {}); // silently ignore if backend unavailable
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
      <div class="offer-card">
        <div class="offer-icon">
          <i class="fas fa-tag"></i>
        </div>
        <div class="offer-content">
          <div class="offer-title">Special Offer</div>
          <div class="offer-message">${message}</div>
          <button class="offer-btn" onclick="handleCTA()">Claim Offer</button>
        </div>
        <div class="offer-close" onclick="this.parentElement.parentElement.remove()">&times;</div>
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
    setTimeout(() => { getDecision(); }, 1000);
  });

  // ----------------------------
  // CLICK TRACKING
  // ----------------------------
  document.addEventListener("click", () => {
    sendEvent("click");
  });

})();

// ----------------------------
// CTA HANDLER (global scope)
// ----------------------------
function handleCTA() {
  fetch("https://pulse-marketing.onrender.com/track", {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    session_id: sessionId,
    event_type: "click",
    page_url: window.location.href,
    timestamp: new Date().toISOString()
  })
});
  

  alert("Redirecting to your offer...");
  setTimeout(() => { window.location.href = "https://amazon.com"; }, 1000);
}