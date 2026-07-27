frappe.ui.form.on('Job Work Order', {
	setup: function(frm) {
		frm.set_query('contractor', 'processes', function(doc, cdt, cdn) {
			return { filters: { 'status': 'Active' } };
		});
	},

	onload: function(frm) {
		if (frm.doc.__islocal) return;
		populate_child_tables(frm);
	},

	refresh: function(frm) {
		if (frm.doc.__islocal) return;

		if (frm.doc.processes && frm.doc.processes.length > 0) {
			refresh_process_numbers(frm);
		} else if (!frm._fetched) {
			// Only fetch once to avoid duplicate API calls
			frm._fetched = true;
			populate_child_tables(frm);
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

/**
 * Main entry point: populate child tables from available data sources.
 * Priority: 1) frm.doc (already loaded), 2) frm.__onload (server-side), 3) API call
 */
function populate_child_tables(frm) {
	// Strategy 1: Data already on the document (e.g., during creation/editing)
	if (frm.doc.processes && frm.doc.processes.length > 0) {
		refresh_process_numbers(frm);
		return;
	}

	// Strategy 2: Data from __onload (set by Python onload() via set_onload)
	var processes = frm.__onload && frm.__onload.jwo_processes;
	var returns = frm.__onload && frm.__onload.jwo_returns;

	if (processes && processes.length > 0) {
		fill_child_grid(frm, 'processes', 'Job Work Order Process', processes, function(child, row, i) {
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
		refresh_process_numbers(frm);
		return;
	}

	// Also populate returns if available
	if (returns && returns.length > 0) {
		fill_child_grid(frm, 'job_work_returns', 'Job Work Return', returns, function(child, row) {
			child.date_received = row.date_received || '';
			child.qty_received = row.qty_received || 0;
			child.qty_rejected = row.qty_rejected || 0;
			child.wastage_qty = row.wastage_qty || 0;
			child.wastage_reason = row.wastage_reason || '';
		});
	}

	// Strategy 3: Fetch from server via API
	if (!frm._api_called) {
		frm._api_called = true;
		fetch_child_data(frm);
	}
}

/**
 * Fill a child table grid with data from an array of rows.
 * Uses frappe.model.add_child (low-level, works on submitted docs).
 */
function fill_child_grid(frm, fieldname, child_doctype, data, field_setter) {
	frm.doc[fieldname] = [];
	$.each(data, function(i, row) {
		var child = frappe.model.add_child(frm.doc, child_doctype, fieldname);
		field_setter(child, row, i);
	});
	frm.refresh_field(fieldname);
}

/**
 * Fetch child table data from server via whitelisted API.
 */
function fetch_child_data(frm) {
	frappe.call({
		method: 'textile_tracking.textile.api.get_process_data',
		args: { docname: frm.doc.name },
		callback: function(r) {
			if (!r || !r.message) return;

			var processes = r.message.processes || [];
			if (processes.length > 0 && (!frm.doc.processes || frm.doc.processes.length === 0)) {
				fill_child_grid(frm, 'processes', 'Job Work Order Process', processes, function(child, row, i) {
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
				refresh_process_numbers(frm);
			}

			var returns = r.message.job_work_returns || [];
			if (returns.length > 0 && (!frm.doc.job_work_returns || frm.doc.job_work_returns.length === 0)) {
				fill_child_grid(frm, 'job_work_returns', 'Job Work Return', returns, function(child, row) {
					child.date_received = row.date_received || '';
					child.qty_received = row.qty_received || 0;
					child.qty_rejected = row.qty_rejected || 0;
					child.wastage_qty = row.wastage_qty || 0;
					child.wastage_reason = row.wastage_reason || '';
				});
			}
		},
		error: function(err) {
			console.error('JWO: Failed to load child data:', err);
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
