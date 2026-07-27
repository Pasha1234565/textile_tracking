frappe.ui.form.on('Job Work Order', {
	setup: function(frm) {
		// Make the process grid columns visible and editable after submission
		frm.set_query('contractor', 'processes', function(doc, cdt, cdn) {
			return {
				filters: { 'status': 'Active' }
			};
		});
	},

	refresh: function(frm) {
		// Show process numbers in the grid
		refresh_process_numbers(frm);
	},

	garment_type: function(frm) {
		// When garment type changes, processes will auto-populate via server-side validate
		// Just refresh to show the updated process numbers
		refresh_process_numbers(frm);
	},

	validate: function(frm) {
		// Ensure process numbers are assigned before save
		refresh_process_numbers(frm);
	}
});

// Process grid events
frappe.ui.form.on('Job Work Order Process', {
	processes_add: function(frm, cdt, cdn) {
		// Auto-assign process number for new row
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
		// If contractor rate card exists for this process, auto-fetch rate
		if (row.contractor && row.process_name) {
			frappe.call({
				method: 'frappe.client.get_list',
				args: {
					doctype: 'Contractor Rate Item',
					filters: {
						'parent': row.contractor,
						'subcontract_process': row.process_name
					},
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
		// Auto-fetch rate from contractor's rate card
		if (row.contractor && row.process_name) {
			frappe.call({
				method: 'frappe.client.get_list',
				args: {
					doctype: 'Contractor Rate Item',
					filters: {
						'parent': row.contractor,
						'subcontract_process': row.process_name
					},
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
	// Re-number processes sequentially using frappe.model.set_value for proper reactivity
	var rows = frm.doc.processes || [];
	$.each(rows, function(i, p) {
		if (p.name) {
			frappe.model.set_value(p.doctype, p.name, 'process_no', i + 1);
		} else {
			p.process_no = i + 1;
		}
	});
	if (rows.length > 0) {
		refresh_field('processes');
	}
}
