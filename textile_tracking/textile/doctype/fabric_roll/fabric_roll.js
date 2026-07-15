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
	}
});
