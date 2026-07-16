function compute_estimates_client_side(frm) {
	// Standard fabric requirements (matching the Python dict)
	var fabric_req = {
		'Shirt': { 'S': 1.2, 'M': 1.4, 'L': 1.6, 'XL': 1.8, 'XXL': 2.0 },
		'T-Shirt': { 'S': 0.8, 'M': 1.0, 'L': 1.2, 'XL': 1.4, 'XXL': 1.6 },
		'Blouse': { 'S': 0.7, 'M': 0.8, 'L': 0.9, 'XL': 1.0, 'XXL': 1.1 },
		'Kurta': { 'S': 1.5, 'M': 1.7, 'L': 1.9, 'XL': 2.1, 'XXL': 2.3 },
		'Saree': { 'S': 5.5, 'M': 5.5, 'L': 5.5, 'XL': 5.5, 'XXL': 5.5 },
		'Suit Set': { 'S': 2.5, 'M': 2.8, 'L': 3.1, 'XL': 3.4, 'XXL': 3.7 },
		'Trouser / Pant': { 'S': 1.0, 'M': 1.1, 'L': 1.2, 'XL': 1.3, 'XXL': 1.5 },
		'Skirt': { 'S': 0.8, 'M': 0.9, 'L': 1.0, 'XL': 1.1, 'XXL': 1.2 }
	};

	var gtype = frm.doc.garment_type;
	var gsize = frm.doc.garment_size;
	var length_m = frm.doc.length_meters || 0;
	var rolls = frm.doc.rolls_given_to_contractor || 1;

	var fabric_per = (fabric_req[gtype] && fabric_req[gtype][gsize]) || 0;
	frm.set_value('estimated_fabric_per_garment', fabric_per);

	if (fabric_per > 0 && length_m > 0) {
		var per_roll = Math.floor(length_m / fabric_per);
		frm.set_value('estimated_garments_per_roll', per_roll);
		frm.set_value('total_estimated_garments', per_roll * rolls);
	} else {
		frm.set_value('estimated_garments_per_roll', 0);
		frm.set_value('total_estimated_garments', 0);
	}

	refresh_summary(frm);
}

function refresh_summary(frm) {
	var total_actual = 0;
	if (frm.doc.daily_production && frm.doc.daily_production.length) {
		$.each(frm.doc.daily_production, function(i, row) {
			total_actual += flt(row.garments_produced);
		});
	}
	frm.set_value('actual_total_produced', total_actual);

	var estimated = frm.doc.total_estimated_garments || 0;
	if (estimated > 0) {
		var wastage = ((estimated - total_actual) / estimated) * 100;
		frm.set_value('wastage_percentage', Math.round(wastage * 10) / 10);
	} else {
		frm.set_value('wastage_percentage', 0);
	}
}

// ---- Form Events ----

frappe.ui.form.on('Fabric Roll', {
	refresh: function(frm) {
		// Show QR code as an HTML preview if qr_code_text is populated
		if (frm.doc.qr_code_text) {
			frm.add_custom_button(__('View Digital Passport'), function() {
				window.open(frm.doc.qr_code_text, '_blank');
			}, __('QR Code'));

			// Add a QR code preview using Google Charts API (no external dependency)
			if (!frm.fields_dict['qr_preview_html']) {
				let qr_url = `https://chart.googleapis.com/chart?chs=150x150&cht=qr&chl=${encodeURIComponent(frm.doc.qr_code_text)}&choe=UTF-8`;
				let html = `<div style="text-align:center;padding:10px;border:1px solid #d1d8dd;border-radius:8px;background:#fff;">
					<img src="${qr_url}" style="width:150px;height:150px;display:block;margin:0 auto;" alt="QR Code"/>
										<p style="margin:8px 0 0;font-size:11px;color:#666;">
						Scan to view Digital Product Passport
					</p>
				</div>`;
				frm.set_df_property('qr_code_text', 'description', html);
			}
		}

		// Auto-fetch batch details
		if (frm.doc.raw_material_batch) {
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Raw Material Batch',
					name: frm.doc.raw_material_batch
				},
				callback: function(r) {
					if (r.message) {
						let batch = r.message;
						let info = `
							<div style="padding:8px;background:#f4f9f4;border-radius:6px;border-left:3px solid #2490ef;">
								<strong>${batch.material_type}</strong> — ${batch.origin_country || ''}<br>
								<span style="font-size:11px;color:#666;">
									Supplier: ${batch.supplier || 'N/A'} | 
									Cert: ${batch.certification_type || 'None'}${batch.organic_cert_id ? ' (' + batch.organic_cert_id + ')' : ''} | 
									Grade: ${batch.quality_grade || 'N/A'}
								</span>
							</div>
						`;
						frm.set_df_property('raw_material_batch', 'description', info);
					}
				}
			});
		}

		// Auto-fetch JWO details
		if (frm.doc.job_work_order) {
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Job Work Order',
					name: frm.doc.job_work_order
				},
				callback: function(r) {
					if (r.message) {
						let jwo = r.message;
						frm.set_value('contractor', jwo.contractor);
						// Auto-populate process history from JWO
						if (jwo.subcontract_process && !frm.doc.process_history) {
							let child = frm.add_child('process_history');
							child.process_name = jwo.subcontract_process;
							child.contractor = jwo.contractor;
							child.date_completed = frappe.datetime.now_date();
							child.notes = `Processed via ${jwo.name}`;
							frm.refresh_field('process_history');
						}
					}
				}
			});
		}

		// Recalculate summary on refresh (for saved docs)
		refresh_summary(frm);
	},

	before_save: function(frm) {
		// Auto-generate QR data if roll_number is set
		if (frm.doc.roll_number && !frm.doc.qr_code_text) {
			let site_url = window.location.origin;
			frm.set_value('qr_code_text', `${site_url}/dpp/${frm.doc.name}`);
		}
	},

	roll_number: function(frm) {
		if (frm.doc.roll_number && !frm.doc.qr_code_text) {
			let site_url = window.location.origin;
			frm.set_value('qr_code_text', `${site_url}/dpp/${frm.doc.name}`);
		}
	},

	// ---- New field handlers ----

	garment_type: function(frm) {
		compute_estimates_client_side(frm);
	},

	garment_size: function(frm) {
		compute_estimates_client_side(frm);
	},

	length_meters: function(frm) {
		compute_estimates_client_side(frm);
	},

	rolls_given_to_contractor: function(frm) {
		compute_estimates_client_side(frm);
	}
});

// ---- Child Table Events (Daily Production) ----

frappe.ui.form.on('Fabric Roll Daily Production', {
	garments_produced: function(frm, cdt, cdn) {
		refresh_summary(frm);
	},

	daily_production_add: function(frm, cdt, cdn) {
		// Auto-set the date to today for new rows
		frappe.model.set_value(cdt, cdn, 'date', frappe.datetime.now_date());
	},

	daily_production_remove: function(frm, cdt, cdn) {
		refresh_summary(frm);
	}
});
