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

  const taglines = [
    "Exclusive offer tailored for you",
    "Limited-time premium deal",
    "Unlock special savings instantly",
    "Your personalized opportunity awaits"
  ];

  const randomTagline = taglines[Math.floor(Math.random() * taglines.length)];

  const banner = document.createElement("div");
  banner.id = "ai-offer-banner";

  banner.innerHTML = `
    <div class="pulse-offer">
      
      <div class="pulse-header">
        <i class="fas fa-bolt"></i>
        <span>Pulse Recommendation</span>
        <button class="pulse-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
      </div>

      <div class="pulse-body">
        <h3>${randomTagline}</h3>
        <p>${message}</p>
      </div>

      <div class="pulse-footer">
        <button onclick="handleCTA()" class="pulse-btn">
          <i class="fas fa-arrow-right"></i> Claim Offer
        </button>
      </div>

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
const style = document.createElement("style");
style.innerHTML = `
.pulse-offer {
  position: fixed;
  bottom: 25px;
  right: 25px;
  width: 320px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 8px 25px rgba(0,0,0,0.15);
  font-family: 'Segoe UI', sans-serif;
  z-index: 9999;
  overflow: hidden;
}

.pulse-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #0f172a;
  color: #fff;
  padding: 10px 15px;
  font-size: 14px;
}

.pulse-header i {
  margin-right: 8px;
}

.pulse-close {
  background: none;
  border: none;
  color: #fff;
  font-size: 18px;
  cursor: pointer;
}

.pulse-body {
  padding: 15px;
}

.pulse-body h3 {
  margin: 0 0 8px;
  font-size: 16px;
  color: #111827;
}

.pulse-body p {
  margin: 0;
  font-size: 14px;
  color: #4b5563;
}

.pulse-footer {
  padding: 15px;
  text-align: right;
}

.pulse-btn {
  background: #2563eb;
  color: white;
  border: none;
  padding: 8px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.pulse-btn:hover {
  background: #1e40af;
}
`;
document.head.appendChild(style);