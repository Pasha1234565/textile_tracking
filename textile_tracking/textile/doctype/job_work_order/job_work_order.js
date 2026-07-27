frappe.ui.form.on('Job Work Order', {
	setup: function(frm) {
		frm.set_query('contractor', 'processes', function(doc, cdt, cdn) {
			return { filters: { 'status': 'Active' } };
		});
	},

	refresh: function(frm) {
		if (frm.doc.__islocal) return;

		// Update process numbers if data is loaded
		if (frm.doc.processes && frm.doc.processes.length > 0) {
			refresh_process_numbers(frm);
		}
	},

	garment_type: function(frm) {
		refresh_process_numbers(frm);
	},

	validate: function(frm) {
		refresh_process_numbers(frm);
	}
});

// Process grid events
frappe.ui.form.on('Job Work Order Process', {
	processes_add: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		var max_no = 0;
		$.each(frm.doc.processes || [], function(i, p) {
			if (p.process_no && p.process_no > max_no) {
				max_no = p.process_no;
			}
		});
		row.process_no = max_no + 1;
		row.status = 'Not Started';
		refresh_process_numbers(frm);
	},

	processes_remove: function(frm) {
		refresh_process_numbers(frm);
	},

	process_name: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.contractor && row.process_name) {
			frappe.call({
				method: 'frappe.client.get_list',
				args: {
					doctype: 'Contractor Rate Item',
					filters: { 'parent': row.contractor, 'subcontract_process': row.process_name },
					fields: ['rate_per_piece'],
					limit: 1
				},
				callback: function(r) {
					if (r.message && r.message.length) {
						frappe.model.set_value(cdt, cdn, 'rate_per_piece', r.message[0].rate_per_piece);
					}
				}
			});
		}
	},

	contractor: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.contractor && row.process_name) {
			frappe.call({
				method: 'frappe.client.get_list',
				args: {
					doctype: 'Contractor Rate Item',
					filters: { 'parent': row.contractor, 'subcontract_process': row.process_name },
					fields: ['rate_per_piece'],
					limit: 1
				},
				callback: function(r) {
					if (r.message && r.message.length) {
						frappe.model.set_value(cdt, cdn, 'rate_per_piece', r.message[0].rate_per_piece);
					}
				}
			});
		}
	}
});

function refresh_process_numbers(frm) {
	var rows = frm.doc.processes || [];
	$.each(rows, function(i, p) {
		p.process_no = i + 1;
	});
	if (rows.length > 0) {
		refresh_field('processes');
	}
}
