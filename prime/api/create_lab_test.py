import frappe
from prime.api.tests_sts_check import create_tests_sts
from prime.api.errorlog import create_error_log
from datetime import date

@frappe.whitelist()
def create_lab_tests(doc , method = None):
	# try:
	
    if doc.invoiced == 1:
        sam = frappe.get_doc('Sales Invoice', doc.reff_invoice)
    else:
        sam = frappe.get_doc('Sales Order', doc.custom_reff_order)
    lab_test_itmes = []

	# token = get_next_token_number()
    # doc.token_no = token  # Assuming token_no is a field in Sample Collection
    # frappe.db.set_value("Sample Collection", doc.name, "token_no", token)


    for item in sam.items:
        matching_samples = []
        if frappe.db.exists("Lab Test Template" , item.item_code):
            template = frappe.get_doc("Lab Test Template" , item.item_code)
            if template.custom_is_profile:
                for test in template.lab_test_groups:
                    
                    lab_test_itmes.append(test.lab_test_template)
            else:
                lab_test_itmes.append(item.item_code)
        
    create_test(doc , sam, lab_test_itmes)
	# except Exception as e:
	# 	create_error_log("Sample Collection" , doc.name , f"Lab Result Creation Error from Sample Collection for patient {doc.patient}" , str(e))

					
		
	
					
	   
	
	# if hor_lab_test_itmes:

	# 	ho_lab_test = frappe.get_doc({
	# 				'doctype': 'Lab Result',
	# 				'patient' : sam.patient,
	# 				# "sample" : matching_samples[0],
	# 				'practitioner' : sam.ref_practitioner,
	# 				"invoice_no" : sam.name,
	# 				# "lab_ref" : doc.lab_ref,
	# 				'normal_test_items' : hor_lab_test_itmes,
	# 				"reff_collection": doc.name,
				
	# 				"type" : "Hormones",
	# 				"reff_order" : doc.custom_reff_order,
	# 				"reff_invoice" : doc.reff_invoice,
	# 				"invoiced" : doc.invoiced,
	# 				"source_order" : doc.source_order,
	# 				"diagnosis" : get_diagnoisis(doc.patient)
					
	# 				})
	# 	ho_lab_test.insert()

# def get_next_token_number():
#     today = date.today().strftime("%Y-%m-%d")
#     last_token = frappe.db.sql("""
#         SELECT token_no FROM `tabSample Collection`
#         WHERE DATE(creation) = %s
#         ORDER BY token_no DESC LIMIT 1
#     """, (today,), as_dict=True)

#     if last_token and last_token[0].get("token_no"):
#         try:
#             last_num = int(last_token[0]["token_no"])
#             return f"{last_num + 1:03}"
#         except:
#             return "001"
#     else:
#         return "001"


def create_test(doc ,sam,  tests):
	lab_test_itmes = []
	urine_lab_test_itmes = []
	hor_lab_test_itmes = []
	matching_samples = []
	for item in tests:
		if frappe.db.exists("Lab Test Template" , item):
			template = frappe.get_doc("Lab Test Template" , item)
			# age_ranges = template.rangs
			dob = frappe.db.get_value("Patient" , doc.patient , "dob")
			sex = frappe.db.get_value("Patient" , doc.patient , "sex")
			current_date = frappe.utils.getdate()
			# age = extract_age_from_dob(str(dob))
			# frappe.errprint(age)
			# frappe.errprint(sex)
			# frappe.errprint(item)
			if template.department:
				# normal_range = get_reff_range(age , sex,  age_ranges , doc.name)
				# frappe.errprint(normal_range)
				sample = ''
				matching_samples = [test.sample for test in doc.lab_test if test.lab_test == template.name]
				if len(matching_samples):
					sample = matching_samples[0]
				if template.lab_test_template_type == "Single"  or template.check_up:
					if template.check_up:
						others = frappe.get_doc("Lab Test Template" , template.name)
						if others.lab_test_template_type == "Grouped":
							for te in others.lab_test_groups:
								
								single_test = frappe.get_doc("Lab Test Template" , te.lab_test_template)
								# age_ranges = single_test.rangs
								
								# normal_range = get_reff_range(age , sex,  age_ranges , doc.name)
								# matching_samples = [test.sample for test in doc.lab_test if test.lab_test == single_test.name]
								# if len(matching_samples):
								# 	sample = matching_samples[0]
								lab_test_itmes.append(
								{
									"test" : single_test.lab_test_name,
									"lab_test_name": single_test.lab_test_name,
									"lab_test_uom": single_test.lab_test_uom,
									"secondary_uom": single_test.secondary_uom,
									"conversion_factor": single_test.conversion_factor,
									# "normal_range": template.lab_test_normal_range,
									"normal_range" :  single_test.lab_test_normal_range,
									"custom_sample" : sample,
									
									
									"require_result_value": 1,
									"allow_blank ":0
								}
							)
					

					else:
						lab_test_itmes.append(
								{
									"test" : template.lab_test_name,
									"lab_test_name": template.lab_test_name,
									"lab_test_uom": template.lab_test_uom,
									"secondary_uom": template.secondary_uom,
									"conversion_factor": template.conversion_factor,
									# "normal_range": template.lab_test_normal_range,
									"normal_range" :  template.lab_test_normal_range,
									"custom_sample" : sample,
									
									
									"require_result_value": 1,
									"allow_blank ":0
								}
							)

			
				if template.lab_test_template_type == "Compound":
					cbc_lab_test_itmes = []
					# cbc_lab_test_itmes.append({
							
						
					# 		"test" : template.name,
						
					# 		"template": template.name

					# 		})
					# if template.name == "Stool Examination":
					
					for normal_test_template in template.normal_test_templates:
					# normal = {}
					# if is_group:
					# 	normal.lab_test_event = normal_test_template.lab_test_event
						# else:

						cbc_lab_test_itmes.append({

							
							"lab_test_event": normal_test_template.lab_test_event,
							

							"lab_test_uom": normal_test_template.lab_test_uom,
							"secondary_uom": normal_test_template.secondary_uom,
							"conversion_factor": normal_test_template.conversion_factor,
							"normal_range": normal_test_template.normal_range,
							"require_result_value": 1,
							"allow_blank": normal_test_template.allow_blank,
							"template": template.name
						})
					if template.name in ["Complete Blood Count","Complete Blood Count (CBC) + ESR"]:
						cbc = 1
					else:
						cbc = 0

					lab_test = frappe.get_doc({
					'doctype': 'Lab Result',
					'patient' : sam.patient,
					# 'token_no': get_next_token_number(),
					"sample" : sample,
					'practitioner' : sam.ref_practitioner,
					"invoice_no" : sam.name,
					"lab_ref" : doc.lab_ref,
					'normal_test_items' : cbc_lab_test_itmes,
					"template" : template.name,
					"lab_test_name" : template.name,
					"type" : "Group",
					"reff_collection": doc.name,
					"reff_order" : doc.custom_reff_order,
					"reff_invoice" : doc.reff_invoice,
					"invoiced" : doc.invoiced,
					"source_order" : doc.source_order,
					"diagnosis" : get_diagnoisis(doc.patient),
					"cbc": cbc
					
					})
					lab_test.insert()
					create_tests_sts(lab_test.doctype , lab_test.name)

				elif template.lab_test_template_type == "Grouped"  and not template.check_up: 
					
			
					
					urine_lab_test_itmes = []
					# if template.name == "Stool Examination":
					
					for normal_test_template in template.lab_test_groups:
						# normal = {}
						# if is_group:
						# 	normal.lab_test_event = normal_test_template.lab_test_event
						# else:
						urine_lab_test_itmes.append({
							
						
							"test" : template.name,
							"lab_test_name" : normal_test_template.lab_test_template,
							"template": template.name

							})
						group_test = frappe.get_doc("Lab Test Template" , normal_test_template.lab_test_template)
						for test in group_test.normal_test_templates:
							urine_lab_test_itmes.append({

							
								"lab_test_event": test.lab_test_event,
								
								
								"lab_test_uom": test.lab_test_uom,
								"secondary_uom": test.secondary_uom,
								"conversion_factor": test.conversion_factor,
								"normal_range": test.normal_range,
								"require_result_value": 1,
								"allow_blank": test.allow_blank,
								"template": normal_test_template.lab_test_template
							})

					lab_test = frappe.get_doc({
					'doctype': 'Lab Result',
					'patient' : sam.patient,
					"sample" : sample,
					'practitioner' : sam.ref_practitioner,
					"invoice_no" : sam.name,
					"lab_ref" : doc.lab_ref,
					'normal_test_items' : urine_lab_test_itmes,
					"template" : template.name,
					"lab_test_name" : template.name,
					"type" : "Group",
					"reff_collection": doc.name,
					"reff_order" : doc.custom_reff_order,
					"reff_invoice" : doc.reff_invoice,
					"invoiced" : doc.invoiced,
					"source_order" : doc.source_order,
					"diagnosis" : get_diagnoisis(doc.patient)
					
					})
		

		
					lab_test.insert()
					create_tests_sts(lab_test.doctype , lab_test.name)

	if lab_test_itmes :
		lab_test = frappe.get_doc({
			'doctype': 'Lab Result',
			'patient' : sam.patient,
			# "sample" : matching_samples[0],
			# 'token_no': get_next_token_number(),
			
			'practitioner' : sam.ref_practitioner,
			"invoice_no" : sam.name,
			"lab_ref" : doc.lab_ref,
			'normal_test_items' : lab_test_itmes,
			"type" : "Blood",
			"reff_order" : doc.custom_reff_order,
			"reff_invoice" : doc.reff_invoice,
			"invoiced" : doc.invoiced,
			"source_order" : doc.source_order,
			"diagnosis" : get_diagnoisis(doc.patient)
			
			
			})
		
		
		lab_test.insert(ignore_permissions = 1)
		create_tests_sts(lab_test.doctype , lab_test.name)
		

def create_normals(item_code):
	
		template = frappe.get_doc("Lab Test Template" , item_code)
		normal = lab_test.append("normal_test_items")
		normal.lab_test_name = template.lab_test_name
		normal.lab_test_uom = template.lab_test_uom
		normal.secondary_uom = template.secondary_uom
		normal.conversion_factor = template.conversion_factor
		normal.normal_range = template.lab_test_normal_range
		normal.require_result_value = 1
		normal.allow_blank = 0


def check_age_sex_and_type(age, sex, age_type, age_ranges):
	# try:
	
	for age_range in age_ranges:
		if not age_range.sex : 
			p_sex = "" 
			age_range.sex  = ""
		else: p_sex = sex
		age_type = age_type.strip()
		age_range.age_type = age_range.age_type.strip()
		
		if age_range.sex == p_sex and age_range.age_type == age_type:
			
			
			if "-" in age_range.age:
				
				lower, upper = map(int, age_range.age.split('-'))
				if lower <= age <= upper:
					# print(f"Age is in the range {age_range.age}, normal range: {age_range['range']}")
					return age_range.normal_range
			elif ">" in age_range.age:
				
				threshold = int(age_range.age.lstrip(">"))
				
				if age > threshold:
					
					return age_range.normal_range


from dateutil.relativedelta import relativedelta
from datetime import datetime
def  extract_age_from_dob(dob_str):
	dob_date = datetime.strptime(dob_str, "%Y-%m-%d")

	# Calculate age components
	age_years = relativedelta(datetime.now(), dob_date).years
	age_months = relativedelta(datetime.now(), dob_date).months
	age_days = relativedelta(datetime.now(), dob_date).days
	p_age = {"Years": age_years, "Months": age_months, "Days": age_days}
	return p_age


def get_reff_range(p_age , gender ,ranges , docname = None):
	org_gender_value = gender
	
	try:
	
		ref_range = None
		age_day = p_age["Days"]
		
		if p_age['Months']:
			age =  int(p_age["Days"]) +  int(p_age['Months'] * 30)
			p_age["Days"] = age
			
		for i in ranges:
			if i.min_age_unit == "Month" or i.max_age_unit == "Month" :
				p_age["Days"] = age_day
			
			if i.sex:
				gender = org_gender_value
			else:
				
				gender = None
				i.sex = None
			# frappe.msgprint(str(int(p_age[i.min_age_unit]) > int(i.min_age)))
	
			if (int(p_age[i.min_age_unit]) >= int(i.min_age) and  int(p_age[i.max_age_unit]) <= int(i.max_age)) and  i.sex == gender:				
				ref_range = i.normal_range
		if ref_range:
			return ref_range
		else:
			return None
	except Exception as e:
		# frappe.errprint(str(e))
		create_error_log("Sample Collection" , docname , "Ref Range Error " , str(e))

# from datetime import datetime

# def get_date_difference(start_date, end_date):
# 	start_date = datetime.strptime(start_date, "%Y-%m-%d")
# 	end_date = datetime.strptime(end_date, "%Y-%m-%d")

# 	# Calculate the difference between the two dates
# 	delta = end_date - start_date

# 	# Extract years and days
# 	years = delta.days // 365
# 	remaining_days = delta.days % 365
# 	if years :
# 		return {"age" : years , "age_type" : "Year"}
# 	if remaining_days:
# 		return  {"age" : remaining_days , "age_type" : "Day"}
# 	return None


def get_diagnoisis(patient):
	diag = frappe.db.sql(f""" 
	select Date(c.creation) , c.diagnosis from `tabPatient Encounter Diagnosis` c left join `tabPatient Encounter` p on c.parent = p.name WHERE p.patient = '{patient}' and Date(c.creation) = ( select MAX(Date(e.creation))  from `tabPatient Encounter Diagnosis` e left join `tabPatient Encounter` d on e.parent = d.name  WHERE d.patient = '{patient}')  ;
	""", as_dict = 1)
	str_diag = ""
	for d in diag:
		str_diag += d.diagnosis + ' ,'
	return str_diag

