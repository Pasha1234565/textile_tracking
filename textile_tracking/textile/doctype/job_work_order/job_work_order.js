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
		if (frm.doc.__islocal) return;

		// Force reload process data from server to ensure grid populates
		frappe.call({
			method: 'frappe.client.get',
			args: {
				doctype: 'Job Work Order',
				name: frm.doc.name
			},
			callback: function(r) {
				if (r.message && r.message.processes) {
					// Clear and re-set the processes table with server data
					var processes = r.message.processes || [];
					if (processes.length > 0) {
						frm.clear_table('processes');
						$.each(processes, function(i, row) {
							var child = frm.add_child('processes');
							child.process_no = row.process_no || (i + 1);
							child.process_name = row.process_name || '';
							child.contractor = row.contractor || '';
							child.date_sent = row.date_sent || '';
							child.expected_return_date = row.expected_return_date || '';
							child.actual_return_date = row.actual_return_date || '';
							child.status = row.status || 'Not Started';
							child.qty_sent = row.qty_sent || 0;
							child.rate_per_piece = row.rate_per_piece || 0;
							child.notes = row.notes || '';
						});
						refresh_field('processes');
						refresh_process_numbers(frm);
					}
				}
			}
		});

		// Also reload returns data
		frappe.call({
			method: 'frappe.client.get',
			args: {
				doctype: 'Job Work Order',
				name: frm.doc.name
			},
			callback: function(r) {
				if (r.message && r.message.job_work_returns) {
					var returns = r.message.job_work_returns || [];
					if (returns.length > 0) {
						frm.clear_table('job_work_returns');
						$.each(returns, function(i, row) {
							var child = frm.add_child('job_work_returns');
							child.date_received = row.date_received || '';
							child.qty_received = row.qty_received || 0;
							child.qty_rejected = row.qty_rejected || 0;
							child.wastage_qty = row.wastage_qty || 0;
							child.wastage_reason = row.wastage_reason || '';
						});
						refresh_field('job_work_returns');
					}
				}
			}
		});
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
