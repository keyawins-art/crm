import psycopg2
import json
import uuid

products = [
    {
        "name": "Cashew Kernel Grading Machine (50-100kg/hr)",
        "code": "WINS-50-100",
        "description": "AI-powered Cashew Kernel Grading Machine designed for small-scale processors.",
        "category": "hardware",
        "specifications": {
            "Capacity": "50kg/hr & 100Kg/hr",
            "Number of Grades Possible": "7 in a single pass",
            "Breakage": "2% or less Breakage",
            "Defect and Husk Removal": "Yes",
            "Duty Cycle": "24hours",
            "Total Power": "7.5HP total power",
            "Belt Material": "PVC"
        }
    },
    {
        "name": "Industrial Cashew Kernel Grading Machine",
        "code": "WINS-IND",
        "description": "Industrial Cashew Kernel Grading Machines for high-volume processors.",
        "category": "hardware",
        "specifications": {
            "Capacity": "150kg/hr, 200Kg/hr, 250Kg/hr",
            "Number of Grades Possible": "7 in a single pass",
            "Breakage": "2% or less Breakage",
            "Defect and Husk Removal": "Yes",
            "Duty Cycle": "24hours",
            "Total Power": "7.5HP total power",
            "Belt Material": "PVC"
        }
    },
    {
        "name": "Trolley Type Vacuum Packing Machine (25KG)",
        "code": "VPM-TROLLEY",
        "description": "Designed for packing 5 kg to 25 kg cashew kernels and other bulk products in a compact brick shape.",
        "category": "hardware",
        "specifications": {
            "Sealing Length": "640",
            "Phase": "3 Phase",
            "Machine Dimension": "1365 x 750 x 1110",
            "Chamber Dimension": "W 730 x H 750 x D 330",
            "Voltage": "440V-3HP-50Hz",
            "Machine Cycle": "10-80 sec",
            "Number of Seals": "2",
            "Weight": "180",
            "Capacity": "1kg to 25kg cashews",
            "Body Material": "SS and MS both Available",
            "Duty Cycle": "24hrs"
        }
    },
    {
        "name": "Custom Type Vacuum Packing Machine (10-50KG)",
        "code": "VPM-CUSTOM",
        "description": "Custom-Built Trolley Type Vacuum Packing Machine designed for larger packs.",
        "category": "hardware",
        "specifications": {
            "Sealing Length": "640",
            "Phase": "3 Phase",
            "Machine Dimension": "L 1400 x W 750 x H 1650",
            "Chamber Dimension": "L 730 x W 420 x H 1256",
            "Voltage": "440V-3HP-50Hz",
            "Machine Cycle": "10-80 sec",
            "Number of Seals": "2",
            "Weight": "250 Kg",
            "Capacity": "10kg to 60kg",
            "Body Material": "SS 304",
            "Duty Cycle": "24hrs"
        }
    },
    {
        "name": "Table-Top Vacuum Packing Machine",
        "code": "VPM-TABLETOP",
        "description": "Perfect for small packets ranging from 100 gms to 3 kg.",
        "category": "hardware",
        "specifications": {
            "Sealing Length": "500mm",
            "Power": "2.2 KVA",
            "Machine Dimension": "L 525 H 90 W 525 (mm)",
            "Voltage": "220V /440V",
            "Machine Cycle": "10-40sec",
            "Machine Size": "L650 x W575 x H550",
            "Weight": "70 Kg",
            "Capacity": "100gms-3Kgs",
            "Body Material": "SS",
            "Duty Cycle": "24 hrs"
        }
    },
    {
        "name": "Door Type Vacuum Packing Machine (600mm)",
        "code": "VPM-DOOR",
        "description": "Specially designed for the retail market, packing products in a neat brick shape from 250g to 5 kg.",
        "category": "hardware",
        "specifications": {
            "Sealing Length": "600 mm",
            "Power": "2.2 KVA",
            "Machine Dimension": "L 800 x W 640 x H 660 (mm)",
            "Voltage": "220V / 440V (3 Phase, 50Hz)",
            "Machine Cycle": "10-40 sec",
            "Chamber Size": "L 715 x W 155 x H 575 (mm)",
            "Capacity": "250g to 5Kg",
            "Weight": "90 Kg",
            "Number of Sealer Bar": "2",
            "Duty Cycle": "24 hrs",
            "Body Material": "SS / MS",
            "Body Thickness": "Outer 1.2mm & Inner 2mm"
        }
    },
    {
        "name": "External 2 Nozzle-Vacuum Packing Machine 1000",
        "code": "VPM-EXT-2N",
        "description": "Double Nozzle Type Vacuum Packing Machine is designed for heavy-duty, large-scale packaging of bulk products.",
        "category": "hardware",
        "specifications": {
            "Sealing Length": "1000mm x 8 mm",
            "Power": "2.2Kw",
            "Machine Dimension": "LxWxH (1085x1465x1860)",
            "Voltage": "415V--3Ph-50Hz",
            "Machine Cycle": "15sec-40sec",
            "Number of Nozzle": "2",
            "Weight": "150 kg",
            "Capacity": "10kgs to 50kgs",
            "Duty Cycle": "24hrs",
            "Body Material": "Stainless Steel"
        }
    },
    {
        "name": "Double Chamber Vacuum Packing Machine",
        "code": "VPM-DOUBLE",
        "description": "Designed for higher productivity and efficiency with two chambers.",
        "category": "hardware",
        "specifications": {
            "Sealing Length": "600",
            "Machine Dimension": "1550x850x1020mm",
            "Voltage": "440V 60Hz",
            "Machine Cycle": "10-40sec",
            "Chamber Size(Single side)": "610x540x165mm",
            "Weight": "320 Kg",
            "Capacity": "1-8 packets/min",
            "Body Material": "SS",
            "Duty Cycle": "24 hrs"
        }
    }
]

def main():
    conn = psycopg2.connect("dbname=crm_db user=postgres password=password host=localhost")
    cur = conn.cursor()
    
    for p in products:
        p_id = str(uuid.uuid4())
        specs_json = json.dumps(p["specifications"])
        query = """
            INSERT INTO products (id, name, code, description, category, status, list_price, cost_price, currency, specifications, has_inventory, quantity_in_stock, units_sold, is_deleted)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (code) DO UPDATE SET specifications = EXCLUDED.specifications;
        """
        cur.execute(query, (p_id, p["name"], p["code"], p["description"], None, 'ACTIVE', 0, 0, 'INR', specs_json, False, 0, 0, False))
        print(f"Inserted {p['name']}")
        
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
