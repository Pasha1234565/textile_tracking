frappe.ui.form.on('Fabric Wastage Log', {
	qty_sent: function(frm) {
		calculate_wastage_pct(frm);
	},
	wastage_qty: function(frm) {
		calculate_wastage_pct(frm);
	},
	job_work_order: function(frm) {
		if (cur_frm.doc.job_work_order) {
			// Get the first process's contractor from the JWO
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Job Work Order',
					name: cur_frm.doc.job_work_order
				},
				callback: function(r) {
					if (r.message && r.message.processes && r.message.processes.length) {
						// Use the first process's contractor
						var firstContractor = r.message.processes[0].contractor;
						if (firstContractor) {
							frm.set_value('contractor', firstContractor);
						}
					}
				}
			});
		}
	}
});

function calculate_wastage_pct(frm) {
	var qty_sent = flt(frm.doc.qty_sent);
	var wastage_qty = flt(frm.doc.wastage_qty);

	if (qty_sent > 0) {
		var pct = (wastage_qty / qty_sent) * 100;
		frm.set_value('wastage_pct', flt(pct, 2));
	} else {
		frm.set_value('wastage_pct', 0);
	}
}
