frappe.pages["ai-assistant"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "AI Assistant",
		single_column: true,
	});

	$(page.body).append(
		'<style>'
		+ '.ai-wrap{display:flex;flex-direction:column;height:calc(100vh - 130px);max-width:860px;margin:0 auto;}'
		+ '.ai-messages{flex:1;overflow-y:auto;padding:24px 20px;display:flex;flex-direction:column;gap:14px;}'
		+ '.ai-msg{max-width:78%;padding:12px 16px;border-radius:14px;line-height:1.6;word-wrap:break-word;white-space:pre-wrap;font-size:0.95rem;}'
		+ '.ai-msg-user{align-self:flex-end;background:#0066cc;color:#fff;border-bottom-right-radius:4px;}'
		+ '.ai-msg-bot{align-self:flex-start;background:#f4f5f7;color:#212529;border-bottom-left-radius:4px;}'
		+ '.ai-msg-thinking{align-self:flex-start;background:#f4f5f7;color:#999;font-style:italic;border-bottom-left-radius:4px;}'
		+ '.ai-footer{display:flex;gap:10px;padding:14px 20px;border-top:1px solid #dee2e6;background:#fff;}'
		+ '.ai-footer input{flex:1;font-size:0.97rem;padding:10px 14px;border-radius:8px;}'
		+ '.ai-footer .btn{min-width:80px;border-radius:8px;}'
		+ '.ai-welcome{color:#888;font-size:0.9rem;text-align:center;margin-top:60px;}'
		+ '</style>'
	);

	$(page.body).append(
		'<div class="ai-wrap">'
		+ '<div class="ai-messages" id="ai-msgs">'
		+ '<div class="ai-msg ai-msg-bot">'
		+ 'Hello! I am your AI assistant for Alihsan Hospital.\n\n'
		+ 'You can ask me questions like:\n'
		+ '- "How many patients were registered this month?"\n'
		+ '- "Show me today\'s open appointments"\n'
		+ '- "What is the total unpaid invoices?"\n\n'
		+ 'Or give me instructions like:\n'
		+ '- "Register a patient named Ayoub, male, age 25"\n'
		+ '- "Create an appointment for patient PAT-00123"'
		+ '</div>'
		+ '</div>'
		+ '<div class="ai-footer">'
		+ '<input type="text" class="form-control" id="ai-input" placeholder="Ask a question or give an instruction..." autocomplete="off">'
		+ '<button class="btn btn-primary" id="ai-send">Send</button>'
		+ '</div>'
		+ '</div>'
	);

	var history = [];
	var $msgs  = $(page.body).find("#ai-msgs");
	var $input = $(page.body).find("#ai-input");
	var $send  = $(page.body).find("#ai-send");

	$input.focus();

	function escHtml(str) {
		return frappe.utils.escape_html(String(str || ""));
	}

	function appendMsg(role, text) {
		var cls = role === "user" ? "ai-msg ai-msg-user" : "ai-msg ai-msg-bot";
		var $m = $('<div></div>').addClass(cls).text(text);
		$msgs.append($m);
		$msgs.scrollTop($msgs[0].scrollHeight);
		return $m;
	}

	function setLoading(on) {
		$send.prop("disabled", on).text(on ? "..." : "Send");
		$input.prop("disabled", on);
	}

	function send() {
		var msg = $input.val().trim();
		if (!msg) return;
		$input.val("");
		appendMsg("user", msg);

		var $thinking = $('<div class="ai-msg ai-msg-thinking">Thinking…</div>');
		$msgs.append($thinking);
		$msgs.scrollTop($msgs[0].scrollHeight);

		setLoading(true);

		frappe.call({
			method: "prime.api.ai.chat",
			args: {
				message: msg,
				history: JSON.stringify(history)
			},
			timeout: 120,
			callback: function (r) {
				$thinking.remove();
				if (r.message) {
					appendMsg("bot", r.message.reply);
					history = r.message.history || [];
					if (history.length > 20) {
						history = history.slice(history.length - 20);
					}
				} else {
					appendMsg("bot", "No response received. Please try again.");
				}
				setLoading(false);
				$input.focus();
			},
			error: function () {
				$thinking.remove();
				appendMsg("bot", "Something went wrong. Please check the console and try again.");
				setLoading(false);
				$input.focus();
			}
		});
	}

	$send.on("click", send);
	$input.on("keydown", function (e) {
		if (e.key === "Enter" && !e.shiftKey) send();
	});
};
