frappe.ui.form.on('Job Work Order', {
	setup: function(frm) {
		frm.set_query('contractor', 'processes', function(doc, cdt, cdn) {
			return { filters: { 'status': 'Active' } };
		});
	},

	onload: function(frm) {
		if (frm.doc.__islocal) return;
		populate_from_onload(frm);
	},

	refresh: function(frm) {
		if (frm.doc.__islocal) return;

		// Try populating from __onload data if grid is still empty
		var hasData = frm.doc.processes && frm.doc.processes.length > 0;
		if (!hasData) {
			populate_from_onload(frm);
		}

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

function populate_from_onload(frm) {
	// Populate processes from __onload data (set by server-side onload hook)
	if (frm.__onload && frm.__onload.processes && frm.__onload.processes.length > 0) {
		var needsLoad = !frm.doc.processes || frm.doc.processes.length === 0;
		if (needsLoad) {
			frm.doc.processes = [];
			$.each(frm.__onload.processes, function(i, row) {
				var child = frappe.model.add_child(frm.doc, 'Job Work Order Process', 'processes');
				child.process_no = row.process_no || row.idx || (i + 1);
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
			frm.refresh_field('processes');
		}
	}

	// Populate returns from __onload
	if (frm.__onload && frm.__onload.job_work_returns && frm.__onload.job_work_returns.length > 0) {
		var needsLoad = !frm.doc.job_work_returns || frm.doc.job_work_returns.length === 0;
		if (needsLoad) {
			frm.doc.job_work_returns = [];
			$.each(frm.__onload.job_work_returns, function(i, row) {
				var child = frappe.model.add_child(frm.doc, 'Job Work Return', 'job_work_returns');
				child.date_received = row.date_received || '';
				child.qty_received = row.qty_received || 0;
				child.qty_rejected = row.qty_rejected || 0;
				child.wastage_qty = row.wastage_qty || 0;
				child.wastage_reason = row.wastage_reason || '';
			});
			frm.refresh_field('job_work_returns');
		}
	}
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
