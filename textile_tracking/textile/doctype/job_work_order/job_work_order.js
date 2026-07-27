frappe.ui.form.on('Job Work Order', {
	setup: function(frm) {
		frm.set_query('contractor', 'processes', function(doc, cdt, cdn) {
			return { filters: { 'status': 'Active' } };
		});
	},

	onload: function(frm) {
		if (frm.doc.__islocal) return;
		// Try loading process data using stored method or __onload
		load_process_data(frm);
	},

	refresh: function(frm) {
		if (frm.doc.__islocal) return;

		var hasData = frm.doc.processes && frm.doc.processes.length > 0;

		if (hasData) {
			refresh_process_numbers(frm);
		} else {
			// Fallback: if grid is still empty, try loading from __onload or DB
			load_process_data(frm);
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

function load_process_data(frm) {
	// First try: data might already be on the doc from onload hook
	if (frm.doc.processes && frm.doc.processes.length > 0) {
		refresh_process_numbers(frm);
		return;
	}

	// Fallback: fetch from server via whitelisted API
	frappe.call({
		method: 'textile_tracking.textile.api.get_process_data',
		args: { docname: frm.doc.name },
		callback: function(r) {
			if (!r || !r.message) return;

			var processes = r.message.processes || [];
			if (processes.length > 0) {
				// Clear and re-populate processes
				frm.clear_table('processes');
				$.each(processes, function(i, row) {
					var child = frm.add_child('processes');
					frappe.model.set_value(child.doctype, child.name, 'process_no', row.process_no || row.idx || (i + 1));
					frappe.model.set_value(child.doctype, child.name, 'process_name', row.process_name || '');
					frappe.model.set_value(child.doctype, child.name, 'contractor', row.contractor || '');
					frappe.model.set_value(child.doctype, child.name, 'date_sent', row.date_sent || '');
					frappe.model.set_value(child.doctype, child.name, 'expected_return_date', row.expected_return_date || '');
					frappe.model.set_value(child.doctype, child.name, 'actual_return_date', row.actual_return_date || '');
					frappe.model.set_value(child.doctype, child.name, 'status', row.status || 'Not Started');
					frappe.model.set_value(child.doctype, child.name, 'qty_sent', row.qty_sent || 0);
					frappe.model.set_value(child.doctype, child.name, 'rate_per_piece', row.rate_per_piece || 0);
					frappe.model.set_value(child.doctype, child.name, 'notes', row.notes || '');
				});
				frm.refresh_field('processes');
			}

			var returns = r.message.job_work_returns || [];
			if (returns.length > 0) {
				frm.clear_table('job_work_returns');
				$.each(returns, function(i, row) {
					var child = frm.add_child('job_work_returns');
					frappe.model.set_value(child.doctype, child.name, 'date_received', row.date_received || '');
					frappe.model.set_value(child.doctype, child.name, 'qty_received', row.qty_received || 0);
					frappe.model.set_value(child.doctype, child.name, 'qty_rejected', row.qty_rejected || 0);
					frappe.model.set_value(child.doctype, child.name, 'wastage_qty', row.wastage_qty || 0);
					frappe.model.set_value(child.doctype, child.name, 'wastage_reason', row.wastage_reason || '');
				});
				frm.refresh_field('job_work_returns');
			}
		},
		error: function(err) {
			console.error('Failed to load JWO child data:', err);
		}
	});
}

function refresh_process_numbers(frm) {
	var rows = frm.doc.processes || [];
	$.each(rows, function(i, p) {
		p.process_no = i + 1;
	});
	if (rows.length > 0) {
		refresh_field('processes');
	}
}
