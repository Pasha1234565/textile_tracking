frappe.ui.form.on('Fabric Wastage Log', {
	qty_sent: function(frm) {
		calculate_wastage_pct(frm);
	},
	wastage_qty: function(frm) {
		calculate_wastage_pct(frm);
	},
	job_work_order: function(frm) {
		if (cur_frm.doc.job_work_order) {
			frappe.db.get_value('Job Work Order', cur_frm.doc.job_work_order, 'contractor', function(r) {
				if (r && r.contractor) {
					frm.set_value('contractor', r.contractor);
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
