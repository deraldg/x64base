-- Full rebuildable SQLite dump for Cascade Precision Mfg ERP Phase 2
BEGIN TRANSACTION;
CREATE TABLE AP_Invoices (
    AP_Invoice_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Vendor_ID INTEGER REFERENCES Vendors(Vendor_ID),
    Invoice_Number TEXT NOT NULL,
    Invoice_Date TEXT NOT NULL,
    Due_Date TEXT NOT NULL,
    Total_Amount REAL NOT NULL,
    Amount_Paid REAL DEFAULT 0,
    Status TEXT CHECK (Status IN ('OPEN','PARTIAL','PAID','VOID')),
    PO_ID INTEGER REFERENCES Purchase_Orders(PO_ID)
);
INSERT INTO "AP_Invoices" VALUES(1,1,'INV-STL-2601','2026-03-14','2026-04-13',2600.0,2600.0,'PAID',1);
INSERT INTO "AP_Invoices" VALUES(2,2,'INV-CAST-2602','2026-03-19','2026-05-03',1530.0,0.0,'OPEN',2);
INSERT INTO "AP_Invoices" VALUES(3,3,'INV-SEAL-2603','2026-03-10','2026-04-09',1912.5,1000.0,'PARTIAL',3);
INSERT INTO "AP_Invoices" VALUES(4,4,'INV-MOTOR-2604','2026-03-15','2026-04-14',3700.0,0.0,'OPEN',4);
INSERT INTO "AP_Invoices" VALUES(5,5,'INV-PKG-2605','2026-03-12','2026-03-27',975.0,975.0,'PAID',5);
INSERT INTO "AP_Invoices" VALUES(6,6,'INV-MRO-2606','2026-03-15','2026-04-14',1010.0,1010.0,'PAID',6);
CREATE TABLE AP_Payments (
    Payment_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    AP_Invoice_ID INTEGER NOT NULL REFERENCES AP_Invoices(AP_Invoice_ID),
    Payment_Date TEXT NOT NULL,
    Amount REAL NOT NULL,
    Method TEXT CHECK (Method IN ('CHECK','ACH','WIRE')),
    Check_Number TEXT
);
INSERT INTO "AP_Payments" VALUES(1,1,'2026-03-28',2600.0,'ACH','ACH-260001');
INSERT INTO "AP_Payments" VALUES(2,3,'2026-03-30',1000.0,'CHECK','10244');
INSERT INTO "AP_Payments" VALUES(3,5,'2026-03-20',975.0,'ACH','ACH-260005');
INSERT INTO "AP_Payments" VALUES(4,6,'2026-03-22',1010.0,'CHECK','10245');
CREATE TABLE AR_Invoices (
    AR_Invoice_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Customer_ID INTEGER NOT NULL REFERENCES Customers(Customer_ID),
    Invoice_Number TEXT NOT NULL,
    Invoice_Date TEXT NOT NULL,
    Due_Date TEXT NOT NULL,
    Total_Amount REAL NOT NULL,
    Amount_Paid REAL DEFAULT 0,
    Status TEXT CHECK (Status IN ('OPEN','PARTIAL','PAID','VOID')),
    SO_ID INTEGER REFERENCES Sales_Orders(SO_ID)
);
INSERT INTO "AR_Invoices" VALUES(1,1,'AR-260001','2026-03-25','2026-04-24',2040.0,400.0,'PARTIAL',1);
INSERT INTO "AR_Invoices" VALUES(2,2,'AR-260002','2026-03-28','2026-04-27',1286.5,500.0,'PARTIAL',2);
INSERT INTO "AR_Invoices" VALUES(3,3,'AR-260003','2026-04-05','2026-05-20',1760.0,0.0,'OPEN',3);
INSERT INTO "AR_Invoices" VALUES(4,4,'AR-260004','2026-03-29','2026-04-28',898.25,898.25,'PAID',4);
INSERT INTO "AR_Invoices" VALUES(5,5,'AR-260005','2026-04-15','2026-05-15',965.0,0.0,'OPEN',5);
INSERT INTO "AR_Invoices" VALUES(6,6,'AR-260006','2026-03-20','2026-03-20',256.5,256.5,'PAID',6);
CREATE TABLE AR_Payments (
    Payment_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    AR_Invoice_ID INTEGER NOT NULL REFERENCES AR_Invoices(AR_Invoice_ID),
    Payment_Date TEXT NOT NULL,
    Amount REAL NOT NULL,
    Method TEXT CHECK (Method IN ('CHECK','ACH','WIRE','CREDIT_CARD','CASH')),
    Reference TEXT
);
INSERT INTO "AR_Payments" VALUES(1,2,'2026-04-05',500.0,'ACH','BRP-ACH-0405');
INSERT INTO "AR_Payments" VALUES(2,4,'2026-04-02',898.25,'WIRE','DYN-WIRE-0402');
INSERT INTO "AR_Payments" VALUES(3,6,'2026-03-20',256.5,'CREDIT_CARD','INT-SVC');
INSERT INTO "AR_Payments" VALUES(4,1,'2026-04-10',400.0,'ACH','ALPHA-PARTIAL');
CREATE TABLE BOM_Details (
    BOM_Detail_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    BOM_ID INTEGER NOT NULL REFERENCES BOM_Headers(BOM_ID),
    Component_Item_ID INTEGER NOT NULL REFERENCES Items(Item_ID),
    Qty_Per REAL NOT NULL,
    UOM TEXT DEFAULT 'EA',
    Sequence INTEGER DEFAULT 0,
    Scrap_Pct REAL DEFAULT 0.00,
    Notes TEXT
);
INSERT INTO "BOM_Details" VALUES(1,1,11,1.0,'EA',10,0.0,'Core assembly');
INSERT INTO "BOM_Details" VALUES(2,1,5,1.0,'EA',20,0.0,'Motor assembly');
INSERT INTO "BOM_Details" VALUES(3,1,8,1.0,'EA',30,0.0,'Fasteners');
INSERT INTO "BOM_Details" VALUES(4,1,10,1.0,'EA',40,0.0,'Packaging');
INSERT INTO "BOM_Details" VALUES(5,2,12,1.0,'EA',10,0.0,'Rotor assembly');
INSERT INTO "BOM_Details" VALUES(6,2,2,1.0,'EA',20,0.0,'Pump housing');
INSERT INTO "BOM_Details" VALUES(7,2,3,1.0,'EA',30,1.0,'Seal kit');
INSERT INTO "BOM_Details" VALUES(8,2,10,1.0,'EA',40,0.0,'Packaging');
INSERT INTO "BOM_Details" VALUES(9,3,13,1.0,'EA',10,0.0,'Trim assembly');
INSERT INTO "BOM_Details" VALUES(10,3,7,1.0,'EA',20,0.0,'Valve body');
INSERT INTO "BOM_Details" VALUES(11,3,9,1.0,'EA',30,0.0,'Fittings');
INSERT INTO "BOM_Details" VALUES(12,4,1,1.0,'EA',10,2.0,'Machined shaft');
INSERT INTO "BOM_Details" VALUES(13,4,4,2.0,'EA',20,0.0,'Bearings');
INSERT INTO "BOM_Details" VALUES(14,5,6,1.0,'EA',10,1.0,'Impeller');
CREATE TABLE BOM_Headers (
    BOM_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Item_ID INTEGER NOT NULL REFERENCES Items(Item_ID),
    BOM_Name TEXT NOT NULL,
    Revision TEXT DEFAULT 'A',
    Effective_Date TEXT,
    Status TEXT CHECK (Status IN ('ACTIVE','OBSOLETE','PENDING')),
    UNIQUE (Item_ID, Revision)
);
INSERT INTO "BOM_Headers" VALUES(1,14,'PDU-100 Production BOM','A','2026-01-01','ACTIVE');
INSERT INTO "BOM_Headers" VALUES(2,15,'RP-200 Production BOM','A','2026-01-01','ACTIVE');
INSERT INTO "BOM_Headers" VALUES(3,16,'PV-300 Production BOM','A','2026-01-01','ACTIVE');
INSERT INTO "BOM_Headers" VALUES(4,11,'PDU Core Assembly BOM','A','2026-01-01','ACTIVE');
INSERT INTO "BOM_Headers" VALUES(5,12,'Pump Rotor Assembly BOM','A','2026-01-01','ACTIVE');
CREATE TABLE Customers (
    Customer_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Customer_Code TEXT UNIQUE NOT NULL,
    Customer_Name TEXT NOT NULL,
    Contact_Name TEXT,
    Phone TEXT,
    Email TEXT,
    Address TEXT,
    City TEXT,
    State TEXT,
    Zip TEXT,
    Credit_Limit REAL DEFAULT 0.00,
    Payment_Terms TEXT DEFAULT 'NET30',
    Tax_Exempt INTEGER DEFAULT 0,
    Status TEXT CHECK (Status IN ('ACTIVE','INACTIVE','SUSPENDED')),
    Since_Date TEXT
);
INSERT INTO "Customers" VALUES(1,'CUST-ALPHA','Alpha Robotics','Priya Desai','206-555-3001','purchasing@alpharobotics.example','10 Automation Way','Seattle','WA','98101',75000.0,'NET30',0,'ACTIVE','2020-01-15');
INSERT INTO "Customers" VALUES(2,'CUST-BLUE','Blue River Pumps','Daniel Cho','541-555-3002','orders@blueriver.example','88 Pump House Rd','Bend','OR','97701',55000.0,'NET30',0,'ACTIVE','2021-04-09');
INSERT INTO "Customers" VALUES(3,'CUST-COLUMBIA','Columbia Process Systems','Erin Fox','503-555-3003','buy@columbiaps.example','700 Plant Loop','Portland','OR','97205',90000.0,'NET45',0,'ACTIVE','2019-05-20');
INSERT INTO "Customers" VALUES(4,'CUST-DYNA','Dynatek Marine','Grace Lin','360-555-3004','procure@dynatek.example','402 Harbor Dr','Tacoma','WA','98402',65000.0,'NET30',0,'ACTIVE','2022-02-01');
INSERT INTO "Customers" VALUES(5,'CUST-EVER','Evergreen Hydraulics','Mark Eaton','509-555-3005','ap@everhyd.example','51 Valve Court','Spokane','WA','99201',45000.0,'NET30',0,'ACTIVE','2023-01-11');
INSERT INTO "Customers" VALUES(6,'CUST-FIELD','Field Service Internal','Ops Desk','541-555-3006','service@cascade.example','1000 Millrace Dr','Eugene','OR','97403',0.0,'NET0',1,'ACTIVE','2018-01-01');
CREATE TABLE Departments (
    Dept_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Dept_Code TEXT UNIQUE NOT NULL,
    Dept_Name TEXT NOT NULL,
    Cost_Center TEXT,
    Manager_ID INTEGER REFERENCES Employees(Employee_ID),
    Active INTEGER DEFAULT 1
);
INSERT INTO "Departments" VALUES(1,'EXEC','Executive','100',1,1);
INSERT INTO "Departments" VALUES(2,'FIN','Finance','200',2,1);
INSERT INTO "Departments" VALUES(3,'OPS','Operations','300',3,1);
INSERT INTO "Departments" VALUES(4,'SALES','Sales and CRM','400',4,1);
INSERT INTO "Departments" VALUES(5,'QA','Quality Assurance','500',5,1);
CREATE TABLE Employees (
    Employee_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Employee_Code TEXT UNIQUE NOT NULL,
    First_Name TEXT NOT NULL,
    Last_Name TEXT NOT NULL,
    Dept_ID INTEGER REFERENCES Departments(Dept_ID),
    Position TEXT,
    Hire_Date TEXT NOT NULL,
    Hourly_Rate REAL,
    Annual_Salary REAL,
    Pay_Type TEXT CHECK (Pay_Type IN ('HOURLY','SALARY')),
    Status TEXT CHECK (Status IN ('ACTIVE','LEAVE','TERMINATED','RETIRED')),
    Reports_To INTEGER REFERENCES Employees(Employee_ID),
    Email TEXT,
    Phone TEXT
);
INSERT INTO "Employees" VALUES(1,'E100','Mara','Whitcomb',1,'President','2018-01-08',NULL,142000.0,'SALARY','ACTIVE',NULL,'mara.whitcomb@cascade.example','541-555-0100');
INSERT INTO "Employees" VALUES(2,'E110','Caleb','Norris',2,'Controller','2019-03-18',NULL,99000.0,'SALARY','ACTIVE',1,'caleb.norris@cascade.example','541-555-0101');
INSERT INTO "Employees" VALUES(3,'E120','Iris','Lopez',3,'Plant Manager','2017-06-05',NULL,118000.0,'SALARY','ACTIVE',1,'iris.lopez@cascade.example','541-555-0102');
INSERT INTO "Employees" VALUES(4,'E130','Grant','Okafor',4,'Sales Manager','2020-02-20',NULL,104000.0,'SALARY','ACTIVE',1,'grant.okafor@cascade.example','541-555-0103');
INSERT INTO "Employees" VALUES(5,'E140','Nina','Patel',5,'Quality Manager','2019-11-12',NULL,94000.0,'SALARY','ACTIVE',3,'nina.patel@cascade.example','541-555-0104');
INSERT INTO "Employees" VALUES(6,'E201','Evan','Reed',3,'CNC Lead','2021-04-01',36.5,NULL,'HOURLY','ACTIVE',3,'evan.reed@cascade.example','541-555-0105');
INSERT INTO "Employees" VALUES(7,'E202','Tessa','Kim',3,'Assembler','2022-01-10',29.0,NULL,'HOURLY','ACTIVE',3,'tessa.kim@cascade.example','541-555-0106');
INSERT INTO "Employees" VALUES(8,'E203','Omar','Hale',3,'Test Technician','2021-09-22',31.0,NULL,'HOURLY','ACTIVE',3,'omar.hale@cascade.example','541-555-0107');
INSERT INTO "Employees" VALUES(9,'E204','June','Rivera',3,'Warehouse Coordinator','2020-08-15',28.0,NULL,'HOURLY','ACTIVE',3,'june.rivera@cascade.example','541-555-0108');
INSERT INTO "Employees" VALUES(10,'E205','Victor','Chen',5,'Inspector','2022-05-03',30.0,NULL,'HOURLY','ACTIVE',5,'victor.chen@cascade.example','541-555-0109');
INSERT INTO "Employees" VALUES(11,'E206','Amina','Grant',5,'Inspector','2023-02-14',29.0,NULL,'HOURLY','ACTIVE',5,'amina.grant@cascade.example','541-555-0110');
INSERT INTO "Employees" VALUES(12,'E301','Leah','Brooks',4,'Account Executive','2021-07-12',NULL,76000.0,'SALARY','ACTIVE',4,'leah.brooks@cascade.example','541-555-0111');
INSERT INTO "Employees" VALUES(13,'E302','Simon','Ng',4,'Customer Success','2022-03-07',NULL,72000.0,'SALARY','ACTIVE',4,'simon.ng@cascade.example','541-555-0112');
INSERT INTO "Employees" VALUES(14,'E401','Pavel','Stone',2,'AP Specialist','2021-12-01',27.0,NULL,'HOURLY','ACTIVE',2,'pavel.stone@cascade.example','541-555-0113');
INSERT INTO "Employees" VALUES(15,'E402','Rosa','Mendez',2,'AR Specialist','2022-06-17',27.0,NULL,'HOURLY','ACTIVE',2,'rosa.mendez@cascade.example','541-555-0114');
INSERT INTO "Employees" VALUES(16,'E501','Hank','Miller',3,'Maintenance Tech','2020-10-25',32.0,NULL,'HOURLY','ACTIVE',3,'hank.miller@cascade.example','541-555-0115');
CREATE TABLE GL_Accounts (
    Account_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Account_Code TEXT NOT NULL UNIQUE,
    Account_Name TEXT NOT NULL,
    Account_Type TEXT NOT NULL CHECK (Account_Type IN ('ASSET','LIABILITY','EQUITY','REVENUE','EXPENSE')),
    Normal_Balance TEXT NOT NULL CHECK (Normal_Balance IN ('DEBIT','CREDIT')),
    Parent_ID INTEGER REFERENCES GL_Accounts(Account_ID),
    Active INTEGER DEFAULT 1
);
INSERT INTO "GL_Accounts" VALUES(1,'1000','Cash','ASSET','DEBIT',NULL,1);
INSERT INTO "GL_Accounts" VALUES(2,'1100','Accounts Receivable','ASSET','DEBIT',NULL,1);
INSERT INTO "GL_Accounts" VALUES(3,'1200','Inventory','ASSET','DEBIT',NULL,1);
INSERT INTO "GL_Accounts" VALUES(4,'1300','Work In Process','ASSET','DEBIT',NULL,1);
INSERT INTO "GL_Accounts" VALUES(5,'1400','Fixed Assets','ASSET','DEBIT',NULL,1);
INSERT INTO "GL_Accounts" VALUES(6,'2000','Accounts Payable','LIABILITY','CREDIT',NULL,1);
INSERT INTO "GL_Accounts" VALUES(7,'3000','Owner Equity','EQUITY','CREDIT',NULL,1);
INSERT INTO "GL_Accounts" VALUES(8,'4000','Sales Revenue','REVENUE','CREDIT',NULL,1);
INSERT INTO "GL_Accounts" VALUES(9,'5000','Cost of Goods Sold','EXPENSE','DEBIT',NULL,1);
INSERT INTO "GL_Accounts" VALUES(10,'5100','Payroll Expense','EXPENSE','DEBIT',NULL,1);
INSERT INTO "GL_Accounts" VALUES(11,'5200','Materials Expense','EXPENSE','DEBIT',NULL,1);
INSERT INTO "GL_Accounts" VALUES(12,'5300','Manufacturing Overhead','EXPENSE','DEBIT',NULL,1);
CREATE TABLE GL_Journal (
    Journal_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Entry_Date TEXT NOT NULL,
    Account_ID INTEGER NOT NULL REFERENCES GL_Accounts(Account_ID),
    Description TEXT,
    Debit REAL DEFAULT 0.00,
    Credit REAL DEFAULT 0.00,
    Source_Module TEXT,
    Source_Ref TEXT,
    Period TEXT,
    Posted INTEGER DEFAULT 0
);
INSERT INTO "GL_Journal" VALUES(1,'2026-03-13',3,'Receive PO-260001 inventory',2600.0,0.0,'PROCUREMENT','PO-260001','2026-03',1);
INSERT INTO "GL_Journal" VALUES(2,'2026-03-13',6,'Accrue PO-260001 liability',0.0,2600.0,'PROCUREMENT','PO-260001','2026-03',1);
INSERT INTO "GL_Journal" VALUES(3,'2026-03-28',6,'Pay INV-STL-2601',2600.0,0.0,'FINANCE','INV-STL-2601','2026-03',1);
INSERT INTO "GL_Journal" VALUES(4,'2026-03-28',1,'Cash paid INV-STL-2601',0.0,2600.0,'FINANCE','INV-STL-2601','2026-03',1);
INSERT INTO "GL_Journal" VALUES(5,'2026-03-25',2,'Invoice SO-260001',2040.0,0.0,'SALES','SO-260001','2026-03',1);
INSERT INTO "GL_Journal" VALUES(6,'2026-03-25',8,'Recognize revenue SO-260001',0.0,2040.0,'SALES','SO-260001','2026-03',1);
INSERT INTO "GL_Journal" VALUES(7,'2026-03-25',9,'COGS SO-260001',1040.0,0.0,'SALES','SO-260001','2026-03',1);
INSERT INTO "GL_Journal" VALUES(8,'2026-03-25',3,'Relieve inventory SO-260001',0.0,1040.0,'SALES','SO-260001','2026-03',1);
INSERT INTO "GL_Journal" VALUES(9,'2026-03-18',10,'Payroll accrual',2200.0,0.0,'HR','PR-2603','2026-03',1);
INSERT INTO "GL_Journal" VALUES(10,'2026-03-18',1,'Cash payroll',0.0,2200.0,'HR','PR-2603','2026-03',1);
INSERT INTO "GL_Journal" VALUES(11,'2026-03-20',1,'Cash received AR-260006',256.5,0.0,'FINANCE','AR-260006','2026-03',1);
INSERT INTO "GL_Journal" VALUES(12,'2026-03-20',2,'Clear AR-260006',0.0,256.5,'FINANCE','AR-260006','2026-03',1);
INSERT INTO "GL_Journal" VALUES(13,'2026-03-18',4,'WO-260001 WIP labor/material',1400.0,0.0,'MANUFACTURING','WO-260001','2026-03',1);
INSERT INTO "GL_Journal" VALUES(14,'2026-03-18',3,'Issue inventory to WIP',0.0,1400.0,'MANUFACTURING','WO-260001','2026-03',1);
INSERT INTO "GL_Journal" VALUES(15,'2026-03-22',6,'Pay MRO invoice',1010.0,0.0,'FINANCE','INV-MRO-2606','2026-03',1);
INSERT INTO "GL_Journal" VALUES(16,'2026-03-22',1,'Cash paid MRO invoice',0.0,1010.0,'FINANCE','INV-MRO-2606','2026-03',1);
INSERT INTO "GL_Journal" VALUES(17,'2026-03-29',2,'Invoice SO-260004',898.25,0.0,'SALES','SO-260004','2026-03',1);
INSERT INTO "GL_Journal" VALUES(18,'2026-03-29',8,'Recognize revenue SO-260004',0.0,898.25,'SALES','SO-260004','2026-03',1);
INSERT INTO "GL_Journal" VALUES(19,'2026-03-30',12,'Overhead allocation',750.0,0.0,'MANUFACTURING','MOH-2603','2026-03',1);
INSERT INTO "GL_Journal" VALUES(20,'2026-03-30',1,'Cash overhead payment',0.0,750.0,'MANUFACTURING','MOH-2603','2026-03',1);
CREATE TABLE Inventory_Movements (
    Movement_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Item_ID INTEGER NOT NULL REFERENCES Items(Item_ID),
    Warehouse_ID INTEGER NOT NULL REFERENCES Warehouses(Warehouse_ID),
    Movement_Type TEXT CHECK (Movement_Type IN ('RECEIPT','ISSUE','TRANSFER','ADJUST','RETURN','SCRAP')),
    Qty REAL NOT NULL,
    Unit_Cost REAL,
    Reference_Type TEXT,
    Reference_ID INTEGER,
    Movement_Date TEXT NOT NULL,
    Created_By INTEGER REFERENCES Employees(Employee_ID)
);
INSERT INTO "Inventory_Movements" VALUES(1,1,1,'ISSUE',6.0,48.0,'WO',2,'2026-03-11',7);
INSERT INTO "Inventory_Movements" VALUES(2,2,1,'TRANSFER',7.0,62.0,'WO',3,'2026-03-12',8);
INSERT INTO "Inventory_Movements" VALUES(3,3,1,'ADJUST',8.0,14.5,'WO',4,'2026-03-13',9);
INSERT INTO "Inventory_Movements" VALUES(4,4,1,'RETURN',9.0,8.25,'WO',5,'2026-03-14',10);
INSERT INTO "Inventory_Movements" VALUES(5,5,1,'SCRAP',10.0,185.0,'WO',6,'2026-03-15',11);
INSERT INTO "Inventory_Movements" VALUES(6,6,1,'RECEIPT',11.0,74.0,'PO',1,'2026-03-16',12);
INSERT INTO "Inventory_Movements" VALUES(7,7,1,'ISSUE',12.0,58.0,'WO',2,'2026-03-17',13);
INSERT INTO "Inventory_Movements" VALUES(8,8,1,'TRANSFER',13.0,6.5,'WO',3,'2026-03-18',6);
INSERT INTO "Inventory_Movements" VALUES(9,9,1,'ADJUST',14.0,22.0,'WO',4,'2026-03-19',7);
INSERT INTO "Inventory_Movements" VALUES(10,10,1,'RETURN',15.0,3.25,'WO',5,'2026-03-20',8);
INSERT INTO "Inventory_Movements" VALUES(11,11,1,'SCRAP',16.0,260.0,'WO',6,'2026-03-21',9);
INSERT INTO "Inventory_Movements" VALUES(12,12,1,'RECEIPT',17.0,130.0,'PO',1,'2026-03-22',10);
INSERT INTO "Inventory_Movements" VALUES(13,13,2,'ISSUE',18.0,95.0,'WO',2,'2026-03-23',11);
INSERT INTO "Inventory_Movements" VALUES(14,14,2,'TRANSFER',19.0,520.0,'WO',3,'2026-03-24',12);
INSERT INTO "Inventory_Movements" VALUES(15,15,3,'ADJUST',20.0,340.0,'WO',4,'2026-03-25',13);
INSERT INTO "Inventory_Movements" VALUES(16,16,3,'RETURN',21.0,220.0,'WO',5,'2026-03-26',6);
CREATE TABLE Items (
    Item_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    SKU TEXT UNIQUE NOT NULL,
    Description TEXT NOT NULL,
    UOM TEXT NOT NULL DEFAULT 'EA',
    Item_Type TEXT CHECK (Item_Type IN ('RAW','WIP','FINISHED','MRO','SERVICE')),
    Cost_Method TEXT CHECK (Cost_Method IN ('FIFO','LIFO','AVG','STANDARD')),
    Standard_Cost REAL,
    List_Price REAL,
    Reorder_Point REAL,
    Reorder_Qty REAL,
    Lead_Days INTEGER,
    Category TEXT,
    Active INTEGER DEFAULT 1
);
INSERT INTO "Items" VALUES(1,'RAW-SHAFT-4140','4140 steel shaft blank','EA','RAW','STANDARD',48.0,NULL,20.0,50.0,14,'Raw Metal',1);
INSERT INTO "Items" VALUES(2,'RAW-HOUS-AL','Aluminum housing casting','EA','RAW','STANDARD',62.0,NULL,15.0,40.0,21,'Castings',1);
INSERT INTO "Items" VALUES(3,'RAW-SEAL-KIT','High-pressure seal kit','EA','RAW','FIFO',14.5,NULL,30.0,100.0,7,'Seals',1);
INSERT INTO "Items" VALUES(4,'RAW-BEAR-6205','Precision bearing 6205','EA','RAW','FIFO',8.25,NULL,60.0,200.0,5,'Bearings',1);
INSERT INTO "Items" VALUES(5,'RAW-MOTOR-1HP','1 HP motor assembly','EA','RAW','STANDARD',185.0,NULL,8.0,20.0,28,'Motors',1);
INSERT INTO "Items" VALUES(6,'RAW-IMP-SS','Stainless pump impeller','EA','RAW','STANDARD',74.0,NULL,12.0,25.0,18,'Pump Components',1);
INSERT INTO "Items" VALUES(7,'RAW-VALVEBODY','Valve body casting','EA','RAW','STANDARD',58.0,NULL,14.0,30.0,21,'Castings',1);
INSERT INTO "Items" VALUES(8,'RAW-FAST-KIT','Stainless fastener kit','EA','RAW','AVG',6.5,NULL,50.0,150.0,4,'Hardware',1);
INSERT INTO "Items" VALUES(9,'RAW-HYD-FIT','Hydraulic fitting kit','EA','RAW','AVG',22.0,NULL,30.0,80.0,10,'Fittings',1);
INSERT INTO "Items" VALUES(10,'PKG-CARTON','Product packaging carton','EA','MRO','FIFO',3.25,NULL,100.0,250.0,5,'Packaging',1);
INSERT INTO "Items" VALUES(11,'WIP-PDU-CORE','PDU core assembly','EA','WIP','STANDARD',260.0,NULL,5.0,10.0,0,'WIP',1);
INSERT INTO "Items" VALUES(12,'WIP-PUMP-ROTOR','Pump rotor assembly','EA','WIP','STANDARD',130.0,NULL,5.0,10.0,0,'WIP',1);
INSERT INTO "Items" VALUES(13,'WIP-VALVE-TRIM','Valve trim assembly','EA','WIP','STANDARD',95.0,NULL,5.0,10.0,0,'WIP',1);
INSERT INTO "Items" VALUES(14,'PDU-100','Precision Drive Unit PDU-100','EA','FINISHED','STANDARD',520.0,895.0,4.0,12.0,10,'Drive Units',1);
INSERT INTO "Items" VALUES(15,'RP-200','Rotary Pump RP-200','EA','FINISHED','STANDARD',340.0,640.0,5.0,15.0,10,'Pumps',1);
INSERT INTO "Items" VALUES(16,'PV-300','Precision Valve PV-300','EA','FINISHED','STANDARD',220.0,420.0,6.0,20.0,8,'Valves',1);
INSERT INTO "Items" VALUES(17,'MRO-COOLANT','CNC coolant drum','EA','MRO','AVG',95.0,NULL,3.0,6.0,5,'MRO',1);
INSERT INTO "Items" VALUES(18,'SERV-CAL','Field calibration service','HR','SERVICE','STANDARD',0.0,125.0,0.0,0.0,0,'Service',1);
CREATE TABLE PO_Lines (
    POLine_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    PO_ID INTEGER NOT NULL REFERENCES Purchase_Orders(PO_ID),
    Item_ID INTEGER NOT NULL REFERENCES Items(Item_ID),
    Line_Number INTEGER NOT NULL,
    Qty_Ordered REAL NOT NULL,
    Qty_Received REAL DEFAULT 0,
    Unit_Price REAL NOT NULL,
    Line_Total REAL GENERATED ALWAYS AS (Qty_Ordered * Unit_Price) STORED,
    UNIQUE (PO_ID, Line_Number)
);
INSERT INTO "PO_Lines" VALUES(1,1,1,1,40.0,40.0,48.0);
INSERT INTO "PO_Lines" VALUES(2,1,8,2,100.0,100.0,6.8);
INSERT INTO "PO_Lines" VALUES(3,2,2,1,20.0,10.0,62.0);
INSERT INTO "PO_Lines" VALUES(4,2,7,2,15.0,5.0,58.0);
INSERT INTO "PO_Lines" VALUES(5,3,3,1,75.0,75.0,14.5);
INSERT INTO "PO_Lines" VALUES(6,3,4,2,100.0,100.0,8.25);
INSERT INTO "PO_Lines" VALUES(7,4,5,1,10.0,0.0,185.0);
INSERT INTO "PO_Lines" VALUES(8,4,6,2,25.0,0.0,74.0);
INSERT INTO "PO_Lines" VALUES(9,5,10,1,250.0,250.0,3.25);
INSERT INTO "PO_Lines" VALUES(10,5,8,2,25.0,25.0,6.5);
INSERT INTO "PO_Lines" VALUES(11,6,17,1,6.0,6.0,95.0);
INSERT INTO "PO_Lines" VALUES(12,6,9,2,20.0,20.0,22.0);
CREATE TABLE Payroll_Runs (
    Payroll_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Employee_ID INTEGER NOT NULL REFERENCES Employees(Employee_ID),
    Period_Start TEXT NOT NULL,
    Period_End TEXT NOT NULL,
    Hours_Regular REAL,
    Hours_OT REAL,
    Gross_Pay REAL NOT NULL,
    Tax_Federal REAL,
    Tax_State REAL,
    Tax_FICA REAL,
    Deductions REAL,
    Net_Pay REAL NOT NULL,
    Run_Date TEXT NOT NULL,
    Check_Number TEXT
);
INSERT INTO "Payroll_Runs" VALUES(1,6,'2026-03-01','2026-03-15',80.0,0.0,1695.0,203.4,101.7,129.67,50.0,1220.4,'2026-03-18','PR-2603-001');
INSERT INTO "Payroll_Runs" VALUES(2,7,'2026-03-01','2026-03-15',80.0,0.0,1790.0,214.8,107.4,136.94,50.0,1288.8,'2026-03-18','PR-2603-002');
INSERT INTO "Payroll_Runs" VALUES(3,8,'2026-03-01','2026-03-15',80.0,4.0,1885.0,226.2,113.1,144.2,50.0,1357.2,'2026-03-18','PR-2603-003');
INSERT INTO "Payroll_Runs" VALUES(4,9,'2026-03-01','2026-03-15',80.0,0.0,1980.0,237.6,118.8,151.47,50.0,1425.6,'2026-03-18','PR-2603-004');
INSERT INTO "Payroll_Runs" VALUES(5,10,'2026-03-01','2026-03-15',80.0,0.0,2075.0,249.0,124.5,158.74,50.0,1494.0,'2026-03-18','PR-2603-005');
INSERT INTO "Payroll_Runs" VALUES(6,11,'2026-03-01','2026-03-15',80.0,4.0,2170.0,260.4,130.2,166.0,50.0,1562.4,'2026-03-18','PR-2603-006');
INSERT INTO "Payroll_Runs" VALUES(7,14,'2026-03-01','2026-03-15',80.0,0.0,2265.0,271.8,135.9,173.27,50.0,1630.8,'2026-03-18','PR-2603-007');
INSERT INTO "Payroll_Runs" VALUES(8,15,'2026-03-01','2026-03-15',80.0,0.0,2360.0,283.2,141.6,180.54,50.0,1699.2,'2026-03-18','PR-2603-008');
CREATE TABLE Price_Lists (
    Price_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Item_ID INTEGER NOT NULL REFERENCES Items(Item_ID),
    Customer_ID INTEGER REFERENCES Customers(Customer_ID),
    Price REAL NOT NULL,
    Min_Qty REAL DEFAULT 1,
    Effective_Date TEXT,
    Expiry_Date TEXT
);
INSERT INTO "Price_Lists" VALUES(1,14,NULL,895.0,1.0,'2026-01-01',NULL);
INSERT INTO "Price_Lists" VALUES(2,15,NULL,640.0,1.0,'2026-01-01',NULL);
INSERT INTO "Price_Lists" VALUES(3,16,NULL,420.0,1.0,'2026-01-01',NULL);
INSERT INTO "Price_Lists" VALUES(4,18,NULL,125.0,1.0,'2026-01-01',NULL);
INSERT INTO "Price_Lists" VALUES(5,14,1,870.0,5.0,'2026-01-01',NULL);
INSERT INTO "Price_Lists" VALUES(6,15,2,620.0,3.0,'2026-01-01',NULL);
INSERT INTO "Price_Lists" VALUES(7,16,3,405.0,5.0,'2026-01-01',NULL);
INSERT INTO "Price_Lists" VALUES(8,14,4,890.0,1.0,'2026-01-01',NULL);
INSERT INTO "Price_Lists" VALUES(9,16,5,410.0,2.0,'2026-01-01',NULL);
INSERT INTO "Price_Lists" VALUES(10,18,6,100.0,1.0,'2026-01-01',NULL);
INSERT INTO "Price_Lists" VALUES(11,15,3,615.0,5.0,'2026-01-01',NULL);
INSERT INTO "Price_Lists" VALUES(12,14,2,875.0,2.0,'2026-01-01',NULL);
CREATE TABLE Purchase_Orders (
    PO_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    PO_Number TEXT UNIQUE NOT NULL,
    Vendor_ID INTEGER NOT NULL REFERENCES Vendors(Vendor_ID),
    Order_Date TEXT NOT NULL,
    Expected_Date TEXT,
    Status TEXT CHECK (Status IN ('DRAFT','SENT','PARTIAL','RECEIVED','CLOSED','CANCELLED')),
    Total_Amount REAL DEFAULT 0.00,
    Approved_By INTEGER REFERENCES Employees(Employee_ID),
    Notes TEXT
);
INSERT INTO "Purchase_Orders" VALUES(1,'PO-260001',1,'2026-03-01','2026-03-14','RECEIVED',2600.0,3,'Steel and fasteners');
INSERT INTO "Purchase_Orders" VALUES(2,'PO-260002',2,'2026-03-02','2026-03-23','PARTIAL',2110.0,3,'Castings');
INSERT INTO "Purchase_Orders" VALUES(3,'PO-260003',3,'2026-03-03','2026-03-10','RECEIVED',1912.5,5,'Seals and bearings');
INSERT INTO "Purchase_Orders" VALUES(4,'PO-260004',4,'2026-03-05','2026-04-02','SENT',3700.0,3,'Motors and impellers');
INSERT INTO "Purchase_Orders" VALUES(5,'PO-260005',5,'2026-03-06','2026-03-12','RECEIVED',975.0,9,'Cartons and fasteners');
INSERT INTO "Purchase_Orders" VALUES(6,'PO-260006',6,'2026-03-07','2026-03-15','RECEIVED',1010.0,3,'Coolant and fittings');
CREATE TABLE Quality_Results (
    Result_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Test_ID INTEGER NOT NULL REFERENCES Quality_Tests(Test_ID),
    Reference_Type TEXT NOT NULL CHECK (Reference_Type IN ('WO','PO','RECEIPT')),
    Reference_ID INTEGER NOT NULL,
    Test_Date TEXT NOT NULL,
    Measured_Value REAL,
    Pass_Fail TEXT CHECK (Pass_Fail IN ('PASS','FAIL','HOLD')),
    Inspector_ID INTEGER REFERENCES Employees(Employee_ID),
    Notes TEXT
);
INSERT INTO "Quality_Results" VALUES(1,1,'RECEIPT',6,'2026-03-09',52.01,'PASS',10,'Bearing lot accepted');
INSERT INTO "Quality_Results" VALUES(2,4,'WO',1,'2026-03-17',7.4,'PASS',11,'PDU load normal');
INSERT INTO "Quality_Results" VALUES(3,2,'WO',2,'2026-03-18',20.2,'PASS',10,'Pump flow nominal');
INSERT INTO "Quality_Results" VALUES(4,3,'WO',6,'2026-03-19',0.6,'HOLD',11,'Retest required');
INSERT INTO "Quality_Results" VALUES(5,5,'PO',1,'2026-03-13',21.0,'PASS',10,'Fasteners accepted');
INSERT INTO "Quality_Results" VALUES(6,1,'RECEIPT',2,'2026-03-13',52.08,'FAIL',10,'Two bearings rejected');
CREATE TABLE Quality_Tests (
    Test_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Test_Name TEXT NOT NULL,
    Test_Type TEXT CHECK (Test_Type IN ('INCOMING','IN_PROCESS','FINAL','AUDIT')),
    Item_ID INTEGER REFERENCES Items(Item_ID),
    Specification TEXT,
    Min_Value REAL,
    Max_Value REAL,
    UOM TEXT
);
INSERT INTO "Quality_Tests" VALUES(1,'Incoming Bearing OD','INCOMING',4,'Outer diameter tolerance',51.95,52.05,'MM');
INSERT INTO "Quality_Tests" VALUES(2,'Pump Flow Test','FINAL',15,'Flow rate at nominal pressure',18.0,22.0,'GPM');
INSERT INTO "Quality_Tests" VALUES(3,'Valve Leak Test','FINAL',16,'Leak rate under pressure',0.0,0.5,'CCM');
INSERT INTO "Quality_Tests" VALUES(4,'Drive Unit Load Test','FINAL',14,'Load current under torque',6.0,9.5,'AMP');
INSERT INTO "Quality_Tests" VALUES(5,'Audit Torque Check','AUDIT',8,'Fastener torque',18.0,22.0,'IN-LB');
CREATE TABLE Receiving (
    Receipt_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    PO_ID INTEGER NOT NULL REFERENCES Purchase_Orders(PO_ID),
    POLine_ID INTEGER NOT NULL REFERENCES PO_Lines(POLine_ID),
    Receipt_Date TEXT NOT NULL,
    Qty_Received REAL NOT NULL,
    Qty_Accepted REAL,
    Qty_Rejected REAL DEFAULT 0,
    Inspector_ID INTEGER REFERENCES Employees(Employee_ID),
    Warehouse_ID INTEGER REFERENCES Warehouses(Warehouse_ID),
    Status TEXT CHECK (Status IN ('PENDING','ACCEPTED','REJECTED','PARTIAL'))
);
INSERT INTO "Receiving" VALUES(1,1,1,'2026-03-13',40.0,40.0,0.0,10,1,'ACCEPTED');
INSERT INTO "Receiving" VALUES(2,1,2,'2026-03-13',100.0,98.0,2.0,10,1,'PARTIAL');
INSERT INTO "Receiving" VALUES(3,2,3,'2026-03-18',10.0,10.0,0.0,11,1,'ACCEPTED');
INSERT INTO "Receiving" VALUES(4,2,4,'2026-03-18',5.0,4.0,1.0,11,2,'PARTIAL');
INSERT INTO "Receiving" VALUES(5,3,5,'2026-03-09',75.0,75.0,0.0,10,1,'ACCEPTED');
INSERT INTO "Receiving" VALUES(6,3,6,'2026-03-09',100.0,100.0,0.0,10,1,'ACCEPTED');
INSERT INTO "Receiving" VALUES(7,5,9,'2026-03-11',250.0,250.0,0.0,11,1,'ACCEPTED');
INSERT INTO "Receiving" VALUES(8,6,11,'2026-03-14',6.0,6.0,0.0,10,1,'ACCEPTED');
CREATE TABLE Routings (
    Routing_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Item_ID INTEGER NOT NULL REFERENCES Items(Item_ID),
    Step_Number INTEGER NOT NULL,
    Center_ID INTEGER NOT NULL REFERENCES Work_Centers(Center_ID),
    Operation TEXT NOT NULL,
    Setup_Hours REAL DEFAULT 0.00,
    Run_Hours_Per REAL DEFAULT 0.00,
    Description TEXT,
    UNIQUE (Item_ID, Step_Number)
);
INSERT INTO "Routings" VALUES(1,14,10,1,'Machine shaft',0.5,1.2,'CNC turn and mill');
INSERT INTO "Routings" VALUES(2,14,20,2,'Assemble drive unit',0.4,1.5,'Core and motor assembly');
INSERT INTO "Routings" VALUES(3,14,30,3,'Functional test',0.2,0.6,'Load test');
INSERT INTO "Routings" VALUES(4,14,40,5,'Pack drive unit',0.1,0.2,'Box and label');
INSERT INTO "Routings" VALUES(5,15,10,1,'Machine rotor',0.4,0.9,'Impeller balance cut');
INSERT INTO "Routings" VALUES(6,15,20,2,'Assemble pump',0.4,1.0,'Rotor housing seals');
INSERT INTO "Routings" VALUES(7,15,30,3,'Pressure test',0.2,0.5,'Leak and flow test');
INSERT INTO "Routings" VALUES(8,15,40,5,'Pack pump',0.1,0.2,'Box and label');
INSERT INTO "Routings" VALUES(9,16,10,1,'Machine valve trim',0.3,0.7,'Seat and stem finishing');
INSERT INTO "Routings" VALUES(10,16,20,2,'Assemble valve',0.3,0.8,'Body and trim');
INSERT INTO "Routings" VALUES(11,16,30,3,'Leak test',0.2,0.4,'Pressure retention');
INSERT INTO "Routings" VALUES(12,16,40,5,'Pack valve',0.1,0.2,'Box and label');
CREATE TABLE SO_Lines (
    SOLine_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    SO_ID INTEGER NOT NULL REFERENCES Sales_Orders(SO_ID),
    Item_ID INTEGER NOT NULL REFERENCES Items(Item_ID),
    Line_Number INTEGER NOT NULL,
    Qty_Ordered REAL NOT NULL,
    Qty_Shipped REAL DEFAULT 0,
    Qty_Backordered REAL DEFAULT 0,
    Unit_Price REAL NOT NULL,
    Discount_Pct REAL DEFAULT 0.00,
    Line_Total REAL GENERATED ALWAYS AS (Qty_Ordered * Unit_Price * (1 - Discount_Pct/100)) STORED,
    UNIQUE (SO_ID, Line_Number)
);
INSERT INTO "SO_Lines" VALUES(1,1,14,1,2.0,0.0,0.0,895.0,0.0);
INSERT INTO "SO_Lines" VALUES(2,1,18,2,2.0,0.0,0.0,125.0,0.0);
INSERT INTO "SO_Lines" VALUES(3,2,15,1,2.0,1.0,0.0,640.0,0.0);
INSERT INTO "SO_Lines" VALUES(4,2,10,2,2.0,1.0,0.0,3.25,0.0);
INSERT INTO "SO_Lines" VALUES(5,3,16,1,3.0,0.0,0.0,420.0,0.0);
INSERT INTO "SO_Lines" VALUES(6,3,18,2,4.0,0.0,0.0,125.0,0.0);
INSERT INTO "SO_Lines" VALUES(7,4,14,1,1.0,1.0,0.0,895.0,0.0);
INSERT INTO "SO_Lines" VALUES(8,4,10,2,1.0,1.0,0.0,3.25,0.0);
INSERT INTO "SO_Lines" VALUES(9,5,16,1,2.0,0.0,0.0,420.0,0.0);
INSERT INTO "SO_Lines" VALUES(10,5,18,2,1.0,0.0,0.0,125.0,0.0);
INSERT INTO "SO_Lines" VALUES(11,6,18,1,2.0,2.0,0.0,125.0,0.0);
INSERT INTO "SO_Lines" VALUES(12,6,10,2,2.0,2.0,0.0,3.25,0.0);
CREATE TABLE Sales_Orders (
    SO_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    SO_Number TEXT UNIQUE NOT NULL,
    Customer_ID INTEGER NOT NULL REFERENCES Customers(Customer_ID),
    Order_Date TEXT NOT NULL,
    Required_Date TEXT,
    Ship_Date TEXT,
    Status TEXT CHECK (Status IN ('NEW','CONFIRMED','PICKING','SHIPPED','INVOICED','CLOSED','CANCELLED')),
    Subtotal REAL,
    Tax_Amount REAL,
    Total_Amount REAL,
    Sales_Rep_ID INTEGER REFERENCES Employees(Employee_ID),
    Ship_To_Address TEXT,
    Notes TEXT
);
INSERT INTO "Sales_Orders" VALUES(1,'SO-260001',1,'2026-03-01','2026-03-25',NULL,'CONFIRMED',2040.0,0.0,2040.0,12,'Alpha Robotics dock','MTO PDU order');
INSERT INTO "Sales_Orders" VALUES(2,'SO-260002',2,'2026-03-03','2026-03-28',NULL,'PICKING',1286.5,0.0,1286.5,12,'Blue River Bend','Pump order');
INSERT INTO "Sales_Orders" VALUES(3,'SO-260003',3,'2026-03-07','2026-04-05',NULL,'NEW',1760.0,0.0,1760.0,13,'Columbia Plant','Valve order');
INSERT INTO "Sales_Orders" VALUES(4,'SO-260004',4,'2026-03-10','2026-04-10','2026-03-29','SHIPPED',898.25,0.0,898.25,13,'Dynatek receiving','Single PDU');
INSERT INTO "Sales_Orders" VALUES(5,'SO-260005',5,'2026-03-12','2026-04-15',NULL,'CONFIRMED',965.0,0.0,965.0,12,'Evergreen Dock','Valve and service');
INSERT INTO "Sales_Orders" VALUES(6,'SO-260006',6,'2026-03-15','2026-03-20','2026-03-20','CLOSED',256.5,0.0,256.5,13,'Internal service','Calibration');
CREATE TABLE Shipment_Lines (
    Ship_Line_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Shipment_ID INTEGER NOT NULL REFERENCES Shipments(Shipment_ID),
    SOLine_ID INTEGER NOT NULL REFERENCES SO_Lines(SOLine_ID),
    Qty_Shipped REAL NOT NULL
);
INSERT INTO "Shipment_Lines" VALUES(1,1,3,1.0);
INSERT INTO "Shipment_Lines" VALUES(2,1,4,1.0);
INSERT INTO "Shipment_Lines" VALUES(3,2,7,1.0);
INSERT INTO "Shipment_Lines" VALUES(4,2,8,1.0);
INSERT INTO "Shipment_Lines" VALUES(5,3,11,2.0);
INSERT INTO "Shipment_Lines" VALUES(6,3,12,2.0);
INSERT INTO "Shipment_Lines" VALUES(7,4,1,1.0);
INSERT INTO "Shipment_Lines" VALUES(8,4,2,1.0);
CREATE TABLE Shipments (
    Shipment_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    SO_ID INTEGER NOT NULL REFERENCES Sales_Orders(SO_ID),
    Ship_Date TEXT NOT NULL,
    Carrier TEXT,
    Tracking_No TEXT,
    Warehouse_ID INTEGER REFERENCES Warehouses(Warehouse_ID),
    Status TEXT CHECK (Status IN ('PACKED','SHIPPED','DELIVERED','RETURNED'))
);
INSERT INTO "Shipments" VALUES(1,2,'2026-03-28','UPS Freight','1Z-BRP-2602',3,'SHIPPED');
INSERT INTO "Shipments" VALUES(2,4,'2026-03-29','FedEx Freight','FDX-DYN-2604',3,'DELIVERED');
INSERT INTO "Shipments" VALUES(3,6,'2026-03-20','Internal','INT-SVC-2606',3,'DELIVERED');
INSERT INTO "Shipments" VALUES(4,1,'2026-03-25','UPS Freight','1Z-ALPHA-2601',3,'PACKED');
CREATE TABLE Stock_Levels (
    Stock_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Item_ID INTEGER NOT NULL REFERENCES Items(Item_ID),
    Warehouse_ID INTEGER NOT NULL REFERENCES Warehouses(Warehouse_ID),
    Bin_Location TEXT,
    Qty_OnHand REAL DEFAULT 0,
    Qty_Committed REAL DEFAULT 0,
    Qty_OnOrder REAL DEFAULT 0,
    Last_Count_Date TEXT,
    UNIQUE (Item_ID, Warehouse_ID, Bin_Location)
);
INSERT INTO "Stock_Levels" VALUES(1,1,1,'A-01',43.0,1.0,10.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(2,2,1,'A-02',46.0,2.0,10.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(3,3,1,'A-03',49.0,3.0,10.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(4,4,1,'A-04',52.0,0.0,10.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(5,5,1,'A-05',55.0,1.0,10.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(6,6,1,'A-06',58.0,2.0,10.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(7,7,1,'A-07',61.0,3.0,10.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(8,8,1,'A-08',64.0,0.0,10.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(9,9,1,'A-09',67.0,1.0,10.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(10,10,1,'A-10',70.0,2.0,10.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(11,11,1,'A-11',73.0,3.0,2.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(12,12,1,'A-12',76.0,0.0,2.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(13,13,1,'A-13',79.0,1.0,2.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(14,14,1,'A-14',3.0,1.0,2.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(15,15,1,'A-15',3.0,1.0,2.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(16,16,1,'A-16',3.0,1.0,2.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(17,17,1,'A-17',3.0,1.0,2.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(18,18,1,'A-18',94.0,2.0,2.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(19,2,2,'Q-02',7.0,0.0,0.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(20,3,2,'Q-03',8.0,0.0,0.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(21,4,2,'Q-04',9.0,0.0,0.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(22,7,2,'Q-07',12.0,0.0,0.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(23,9,2,'Q-09',14.0,0.0,0.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(24,17,2,'Q-17',22.0,0.0,0.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(25,14,3,'S-14',5.0,1.0,0.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(26,15,3,'S-15',3.0,1.0,0.0,'2026-03-31');
INSERT INTO "Stock_Levels" VALUES(27,16,3,'S-16',4.0,1.0,0.0,'2026-03-31');
CREATE TABLE Time_Cards (
    TimeCard_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Employee_ID INTEGER NOT NULL REFERENCES Employees(Employee_ID),
    Work_Date TEXT NOT NULL,
    Hours_Regular REAL DEFAULT 0.00,
    Hours_OT REAL DEFAULT 0.00,
    WO_ID INTEGER REFERENCES Work_Orders(WO_ID),
    Center_ID INTEGER REFERENCES Work_Centers(Center_ID),
    Cost_Center TEXT,
    Approved INTEGER DEFAULT 0
);
INSERT INTO "Time_Cards" VALUES(1,6,'2026-03-11',8.0,0.0,1,1,'300',1);
INSERT INTO "Time_Cards" VALUES(2,7,'2026-03-12',8.0,0.0,2,2,'300',1);
INSERT INTO "Time_Cards" VALUES(3,8,'2026-03-13',8.0,0.0,3,3,'500',0);
INSERT INTO "Time_Cards" VALUES(4,9,'2026-03-14',8.0,1.0,4,4,'300',1);
INSERT INTO "Time_Cards" VALUES(5,10,'2026-03-15',8.0,0.0,5,5,'300',1);
INSERT INTO "Time_Cards" VALUES(6,11,'2026-03-16',8.0,0.0,6,1,'300',0);
INSERT INTO "Time_Cards" VALUES(7,16,'2026-03-17',8.0,0.0,1,2,'300',1);
INSERT INTO "Time_Cards" VALUES(8,6,'2026-03-18',8.0,1.0,2,3,'500',1);
INSERT INTO "Time_Cards" VALUES(9,7,'2026-03-19',8.0,0.0,3,4,'300',0);
INSERT INTO "Time_Cards" VALUES(10,8,'2026-03-20',8.0,0.0,4,5,'300',1);
INSERT INTO "Time_Cards" VALUES(11,9,'2026-03-21',8.0,0.0,5,1,'300',1);
INSERT INTO "Time_Cards" VALUES(12,10,'2026-03-22',8.0,1.0,6,2,'300',0);
INSERT INTO "Time_Cards" VALUES(13,11,'2026-03-23',8.0,0.0,1,3,'500',1);
INSERT INTO "Time_Cards" VALUES(14,16,'2026-03-24',8.0,0.0,2,4,'300',1);
CREATE TABLE Vendor_Items (
    Vendor_Item_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Vendor_ID INTEGER NOT NULL REFERENCES Vendors(Vendor_ID),
    Item_ID INTEGER NOT NULL REFERENCES Items(Item_ID),
    Vendor_Part_No TEXT,
    Unit_Price REAL NOT NULL,
    Lead_Days INTEGER DEFAULT 0,
    Min_Order_Qty REAL DEFAULT 1,
    Is_Preferred INTEGER DEFAULT 0,
    UNIQUE (Vendor_ID, Item_ID)
);
INSERT INTO "Vendor_Items" VALUES(1,1,1,'STL-4140-BLANK',48.0,14,10.0,1);
INSERT INTO "Vendor_Items" VALUES(2,1,8,'SS-FAST-KIT',6.5,5,25.0,0);
INSERT INTO "Vendor_Items" VALUES(3,2,2,'AL-HOUS-CAST',62.0,21,5.0,1);
INSERT INTO "Vendor_Items" VALUES(4,2,7,'VALVEBODY-CAST',58.0,21,5.0,1);
INSERT INTO "Vendor_Items" VALUES(5,3,3,'SEAL-HP-KIT',14.5,7,25.0,1);
INSERT INTO "Vendor_Items" VALUES(6,3,4,'BEAR-6205-P',8.25,5,50.0,1);
INSERT INTO "Vendor_Items" VALUES(7,4,5,'MTR-1HP-ASM',185.0,28,2.0,1);
INSERT INTO "Vendor_Items" VALUES(8,4,6,'IMP-SS-200',74.0,18,5.0,1);
INSERT INTO "Vendor_Items" VALUES(9,5,10,'CARTON-PROD',3.25,5,100.0,1);
INSERT INTO "Vendor_Items" VALUES(10,6,17,'COOLANT-55G',95.0,5,1.0,1);
INSERT INTO "Vendor_Items" VALUES(11,6,9,'HYD-FIT-KIT',22.0,10,10.0,0);
INSERT INTO "Vendor_Items" VALUES(12,3,9,'HYD-FIT-ALT',23.5,12,10.0,0);
CREATE TABLE Vendors (
    Vendor_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Vendor_Code TEXT UNIQUE NOT NULL,
    Vendor_Name TEXT NOT NULL,
    Contact_Name TEXT,
    Phone TEXT,
    Email TEXT,
    Address TEXT,
    City TEXT,
    State TEXT,
    Zip TEXT,
    Payment_Terms TEXT DEFAULT 'NET30',
    Rating TEXT CHECK (Rating IN ('A','B','C','D','F')),
    Active INTEGER DEFAULT 1
);
INSERT INTO "Vendors" VALUES(1,'VEND-STEEL','Willamette Steel Supply','Tom Arlen','503-555-2001','orders@willsteel.example','120 River Rd','Salem','OR','97301','NET30','A',1);
INSERT INTO "Vendors" VALUES(2,'VEND-CAST','Pacific Castings','Mia Stone','541-555-2002','sales@pacificcast.example','77 Foundry Way','Eugene','OR','97402','NET45','A',1);
INSERT INTO "Vendors" VALUES(3,'VEND-SEAL','Northwest Seal and Bearing','Ian Scott','360-555-2003','parts@nwseal.example','9 Bearing Ln','Vancouver','WA','98660','NET30','B',1);
INSERT INTO "Vendors" VALUES(4,'VEND-MOTOR','Cascade Motion Components','Lila Park','541-555-2004','csr@cmotion.example','440 Motor Ave','Springfield','OR','97477','NET30','A',1);
INSERT INTO "Vendors" VALUES(5,'VEND-PKG','Emerald Packaging','Nora Blake','541-555-2005','orders@emeraldpkg.example','52 Box St','Eugene','OR','97401','NET15','B',1);
INSERT INTO "Vendors" VALUES(6,'VEND-MRO','Industrial Maintenance Co','Ralph Moon','503-555-2006','desk@imco.example','310 Plant Rd','Portland','OR','97214','NET30','C',1);
CREATE TABLE WO_Materials (
    WO_Material_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    WO_ID INTEGER NOT NULL REFERENCES Work_Orders(WO_ID),
    Item_ID INTEGER NOT NULL REFERENCES Items(Item_ID),
    Qty_Required REAL NOT NULL,
    Qty_Issued REAL DEFAULT 0.00,
    Warehouse_ID INTEGER REFERENCES Warehouses(Warehouse_ID)
);
INSERT INTO "WO_Materials" VALUES(1,1,11,2.0,2.0,1);
INSERT INTO "WO_Materials" VALUES(2,1,5,2.0,1.0,1);
INSERT INTO "WO_Materials" VALUES(3,1,8,2.0,2.0,1);
INSERT INTO "WO_Materials" VALUES(4,1,10,2.0,0.0,1);
INSERT INTO "WO_Materials" VALUES(5,2,12,2.0,2.0,1);
INSERT INTO "WO_Materials" VALUES(6,2,2,2.0,2.0,1);
INSERT INTO "WO_Materials" VALUES(7,2,3,2.0,2.0,1);
INSERT INTO "WO_Materials" VALUES(8,3,13,3.0,0.0,1);
INSERT INTO "WO_Materials" VALUES(9,3,7,3.0,0.0,1);
INSERT INTO "WO_Materials" VALUES(10,3,9,3.0,0.0,1);
INSERT INTO "WO_Materials" VALUES(11,4,11,4.0,3.0,1);
INSERT INTO "WO_Materials" VALUES(12,5,12,5.0,5.0,1);
INSERT INTO "WO_Materials" VALUES(13,6,13,6.0,3.0,1);
INSERT INTO "WO_Materials" VALUES(14,6,7,6.0,3.0,1);
CREATE TABLE WO_Operations (
    WO_Op_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    WO_ID INTEGER NOT NULL REFERENCES Work_Orders(WO_ID),
    Routing_ID INTEGER REFERENCES Routings(Routing_ID),
    Step_Number INTEGER NOT NULL,
    Center_ID INTEGER NOT NULL REFERENCES Work_Centers(Center_ID),
    Status TEXT CHECK (Status IN ('PENDING','IN_PROGRESS','COMPLETED')),
    Actual_Hours REAL DEFAULT 0.00,
    Qty_Good INTEGER DEFAULT 0,
    Qty_Scrap INTEGER DEFAULT 0
);
INSERT INTO "WO_Operations" VALUES(1,1,1,10,1,'COMPLETED',2.5,2,0);
INSERT INTO "WO_Operations" VALUES(2,1,2,20,2,'IN_PROGRESS',1.4,0,0);
INSERT INTO "WO_Operations" VALUES(3,2,5,10,1,'COMPLETED',1.8,2,0);
INSERT INTO "WO_Operations" VALUES(4,2,6,20,2,'IN_PROGRESS',1.1,1,0);
INSERT INTO "WO_Operations" VALUES(5,3,9,10,1,'PENDING',0.0,0,0);
INSERT INTO "WO_Operations" VALUES(6,3,10,20,2,'PENDING',0.0,0,0);
INSERT INTO "WO_Operations" VALUES(7,4,1,10,1,'COMPLETED',4.8,4,0);
INSERT INTO "WO_Operations" VALUES(8,4,2,20,2,'IN_PROGRESS',2.1,2,0);
INSERT INTO "WO_Operations" VALUES(9,5,5,10,1,'COMPLETED',4.7,5,0);
INSERT INTO "WO_Operations" VALUES(10,5,6,20,2,'COMPLETED',4.9,5,0);
INSERT INTO "WO_Operations" VALUES(11,6,9,10,1,'COMPLETED',4.2,5,1);
INSERT INTO "WO_Operations" VALUES(12,6,10,20,2,'IN_PROGRESS',2.2,3,1);
CREATE TABLE Warehouses (
    Warehouse_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Warehouse_Code TEXT UNIQUE NOT NULL,
    Warehouse_Name TEXT NOT NULL,
    Location TEXT,
    Manager_ID INTEGER REFERENCES Employees(Employee_ID)
);
INSERT INTO "Warehouses" VALUES(1,'MAIN','Main Inventory','Eugene Plant A',9);
INSERT INTO "Warehouses" VALUES(2,'QA','Quality Hold','Eugene Plant A',5);
INSERT INTO "Warehouses" VALUES(3,'SHIP','Shipping Staging','Eugene Dock',9);
CREATE TABLE Work_Centers (
    Center_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Center_Code TEXT UNIQUE NOT NULL,
    Center_Name TEXT NOT NULL,
    Department TEXT,
    Capacity_Hours_Day REAL DEFAULT 8.0,
    Hourly_Rate REAL DEFAULT 0.00,
    Status TEXT CHECK (Status IN ('ACTIVE','MAINTENANCE','OFFLINE'))
);
INSERT INTO "Work_Centers" VALUES(1,'CNC','CNC Machining','OPS',16.0,85.0,'ACTIVE');
INSERT INTO "Work_Centers" VALUES(2,'ASM','Final Assembly','OPS',16.0,62.0,'ACTIVE');
INSERT INTO "Work_Centers" VALUES(3,'TEST','Functional Test','QA',8.0,70.0,'ACTIVE');
INSERT INTO "Work_Centers" VALUES(4,'FIN','Paint and Finish','OPS',8.0,55.0,'ACTIVE');
INSERT INTO "Work_Centers" VALUES(5,'PACK','Packaging','OPS',8.0,42.0,'ACTIVE');
CREATE TABLE Work_Orders (
    WO_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    WO_Number TEXT UNIQUE NOT NULL,
    Item_ID INTEGER NOT NULL REFERENCES Items(Item_ID),
    BOM_ID INTEGER REFERENCES BOM_Headers(BOM_ID),
    Qty_Ordered REAL NOT NULL,
    Qty_Completed REAL DEFAULT 0,
    Qty_Scrapped REAL DEFAULT 0,
    Status TEXT CHECK (Status IN ('PLANNED','RELEASED','IN_PROGRESS','COMPLETED','CLOSED','CANCELLED')),
    Priority INTEGER DEFAULT 5,
    Start_Date TEXT,
    Due_Date TEXT,
    Completion_Date TEXT,
    SO_ID INTEGER REFERENCES Sales_Orders(SO_ID),
    Notes TEXT
);
INSERT INTO "Work_Orders" VALUES(1,'WO-260001',14,1,2.0,0.0,0.0,'RELEASED',3,'2026-03-05','2026-03-20',NULL,1,'Make-to-order PDU');
INSERT INTO "Work_Orders" VALUES(2,'WO-260002',15,2,2.0,1.0,0.0,'IN_PROGRESS',4,'2026-03-06','2026-03-22',NULL,2,'Pump order');
INSERT INTO "Work_Orders" VALUES(3,'WO-260003',16,3,3.0,0.0,0.0,'PLANNED',5,NULL,'2026-04-01',NULL,3,'Valve order');
INSERT INTO "Work_Orders" VALUES(4,'WO-260004',14,1,4.0,2.0,0.0,'IN_PROGRESS',5,'2026-03-08','2026-04-08',NULL,NULL,'Make-to-stock PDU');
INSERT INTO "Work_Orders" VALUES(5,'WO-260005',15,2,5.0,5.0,0.0,'COMPLETED',5,'2026-02-20','2026-03-10','2026-03-08',NULL,'Make-to-stock pump');
INSERT INTO "Work_Orders" VALUES(6,'WO-260006',16,3,6.0,3.0,1.0,'IN_PROGRESS',5,'2026-03-01','2026-03-30',NULL,5,'Valve stock and customer demand');
CREATE VIEW v_Available_Stock AS
SELECT
    i.Item_ID,
    i.SKU,
    i.Description,
    i.Item_Type,
    w.Warehouse_Code,
    w.Warehouse_Name,
    s.Bin_Location,
    s.Qty_OnHand,
    s.Qty_Committed,
    s.Qty_OnOrder,
    (s.Qty_OnHand - s.Qty_Committed) AS Available,
    i.Reorder_Point,
    i.Reorder_Qty
FROM Stock_Levels s
JOIN Items i ON i.Item_ID = s.Item_ID
JOIN Warehouses w ON w.Warehouse_ID = s.Warehouse_ID;
CREATE VIEW v_Reorder_Alert AS
SELECT *
FROM v_Available_Stock
WHERE Reorder_Point IS NOT NULL
  AND Available <= Reorder_Point;
CREATE VIEW v_Open_Sales_Orders AS
SELECT
    so.SO_ID,
    so.SO_Number,
    so.Order_Date,
    so.Required_Date,
    so.Status,
    c.Customer_Code,
    c.Customer_Name,
    e.Employee_Code AS Sales_Rep_Code,
    e.First_Name || ' ' || e.Last_Name AS Sales_Rep,
    so.Total_Amount
FROM Sales_Orders so
JOIN Customers c ON c.Customer_ID = so.Customer_ID
LEFT JOIN Employees e ON e.Employee_ID = so.Sales_Rep_ID
WHERE so.Status NOT IN ('CLOSED','CANCELLED');
CREATE VIEW v_Work_Order_Status AS
SELECT
    wo.WO_ID,
    wo.WO_Number,
    i.SKU,
    i.Description,
    wo.Qty_Ordered,
    wo.Qty_Completed,
    wo.Qty_Scrapped,
    wo.Status,
    wo.Start_Date,
    wo.Due_Date,
    so.SO_Number
FROM Work_Orders wo
JOIN Items i ON i.Item_ID = wo.Item_ID
LEFT JOIN Sales_Orders so ON so.SO_ID = wo.SO_ID;
CREATE VIEW v_AP_Aging AS
SELECT
    ap.AP_Invoice_ID,
    ap.Invoice_Number,
    v.Vendor_Code,
    v.Vendor_Name,
    ap.Invoice_Date,
    ap.Due_Date,
    CAST(julianday('now') - julianday(ap.Due_Date) AS INTEGER) AS Days_Past_Due,
    ap.Total_Amount,
    ap.Amount_Paid,
    (ap.Total_Amount - ap.Amount_Paid) AS Balance,
    ap.Status
FROM AP_Invoices ap
LEFT JOIN Vendors v ON v.Vendor_ID = ap.Vendor_ID
WHERE ap.Status IN ('OPEN','PARTIAL');
CREATE VIEW v_AR_Aging AS
SELECT
    ar.AR_Invoice_ID,
    ar.Invoice_Number,
    c.Customer_Code,
    c.Customer_Name,
    ar.Invoice_Date,
    ar.Due_Date,
    CAST(julianday('now') - julianday(ar.Due_Date) AS INTEGER) AS Days_Past_Due,
    ar.Total_Amount,
    ar.Amount_Paid,
    (ar.Total_Amount - ar.Amount_Paid) AS Balance,
    ar.Status
FROM AR_Invoices ar
JOIN Customers c ON c.Customer_ID = ar.Customer_ID
WHERE ar.Status IN ('OPEN','PARTIAL');
CREATE VIEW v_Trial_Balance AS
SELECT
    a.Account_Code,
    a.Account_Name,
    a.Account_Type,
    a.Normal_Balance,
    COALESCE(SUM(j.Debit),0.0) AS Total_Debit,
    COALESCE(SUM(j.Credit),0.0) AS Total_Credit,
    COALESCE(SUM(j.Debit),0.0) - COALESCE(SUM(j.Credit),0.0) AS Net
FROM GL_Accounts a
LEFT JOIN GL_Journal j ON j.Account_ID = a.Account_ID
GROUP BY a.Account_ID, a.Account_Code, a.Account_Name, a.Account_Type, a.Normal_Balance;
CREATE VIEW v_BOM_Explosion AS
SELECT
    bh.BOM_ID,
    parent.SKU AS Parent_SKU,
    parent.Description AS Parent_Description,
    bh.Revision,
    bd.Sequence,
    comp.SKU AS Component_SKU,
    comp.Description AS Component_Description,
    bd.Qty_Per,
    bd.UOM,
    bd.Scrap_Pct
FROM BOM_Headers bh
JOIN Items parent ON parent.Item_ID = bh.Item_ID
JOIN BOM_Details bd ON bd.BOM_ID = bh.BOM_ID
JOIN Items comp ON comp.Item_ID = bd.Component_Item_ID;
CREATE VIEW v_Three_Way_Match AS
SELECT
    po.PO_ID,
    po.PO_Number,
    v.Vendor_Code,
    v.Vendor_Name,
    ROUND(COALESCE(po.Total_Amount,0),2) AS PO_Total,
    ROUND(COALESCE(SUM(r.Qty_Accepted * pl.Unit_Price),0),2) AS Received_Value,
    ROUND(COALESCE(ap.Total_Amount,0),2) AS Invoice_Total,
    CASE
        WHEN ROUND(COALESCE(po.Total_Amount,0),2) = ROUND(COALESCE(SUM(r.Qty_Accepted * pl.Unit_Price),0),2)
         AND ROUND(COALESCE(po.Total_Amount,0),2) = ROUND(COALESCE(ap.Total_Amount,0),2)
        THEN 'MATCHED'
        ELSE 'MISMATCH'
    END AS Match_Status
FROM Purchase_Orders po
JOIN Vendors v ON v.Vendor_ID = po.Vendor_ID
LEFT JOIN PO_Lines pl ON pl.PO_ID = po.PO_ID
LEFT JOIN Receiving r ON r.POLine_ID = pl.POLine_ID
LEFT JOIN AP_Invoices ap ON ap.PO_ID = po.PO_ID
GROUP BY po.PO_ID, po.PO_Number, v.Vendor_Code, v.Vendor_Name, ap.AP_Invoice_ID, ap.Total_Amount;
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('GL_Accounts',12);
INSERT INTO "sqlite_sequence" VALUES('Departments',5);
INSERT INTO "sqlite_sequence" VALUES('Employees',16);
INSERT INTO "sqlite_sequence" VALUES('Vendors',6);
INSERT INTO "sqlite_sequence" VALUES('Customers',6);
INSERT INTO "sqlite_sequence" VALUES('Items',18);
INSERT INTO "sqlite_sequence" VALUES('Warehouses',3);
INSERT INTO "sqlite_sequence" VALUES('Work_Centers',5);
INSERT INTO "sqlite_sequence" VALUES('BOM_Headers',5);
INSERT INTO "sqlite_sequence" VALUES('BOM_Details',14);
INSERT INTO "sqlite_sequence" VALUES('Routings',12);
INSERT INTO "sqlite_sequence" VALUES('Sales_Orders',6);
INSERT INTO "sqlite_sequence" VALUES('SO_Lines',12);
INSERT INTO "sqlite_sequence" VALUES('Work_Orders',6);
INSERT INTO "sqlite_sequence" VALUES('WO_Materials',14);
INSERT INTO "sqlite_sequence" VALUES('WO_Operations',12);
INSERT INTO "sqlite_sequence" VALUES('Vendor_Items',12);
INSERT INTO "sqlite_sequence" VALUES('Purchase_Orders',6);
INSERT INTO "sqlite_sequence" VALUES('PO_Lines',12);
INSERT INTO "sqlite_sequence" VALUES('Receiving',8);
INSERT INTO "sqlite_sequence" VALUES('AP_Invoices',6);
INSERT INTO "sqlite_sequence" VALUES('AP_Payments',4);
INSERT INTO "sqlite_sequence" VALUES('AR_Invoices',6);
INSERT INTO "sqlite_sequence" VALUES('AR_Payments',4);
INSERT INTO "sqlite_sequence" VALUES('Price_Lists',12);
INSERT INTO "sqlite_sequence" VALUES('Stock_Levels',27);
INSERT INTO "sqlite_sequence" VALUES('Inventory_Movements',16);
INSERT INTO "sqlite_sequence" VALUES('Time_Cards',14);
INSERT INTO "sqlite_sequence" VALUES('Payroll_Runs',8);
INSERT INTO "sqlite_sequence" VALUES('Shipments',4);
INSERT INTO "sqlite_sequence" VALUES('Shipment_Lines',8);
INSERT INTO "sqlite_sequence" VALUES('Quality_Tests',5);
INSERT INTO "sqlite_sequence" VALUES('Quality_Results',6);
INSERT INTO "sqlite_sequence" VALUES('GL_Journal',20);
COMMIT;
