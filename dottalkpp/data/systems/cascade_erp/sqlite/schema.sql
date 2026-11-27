-- Cascade Precision Mfg ERP schema - Phase 2 seed package
PRAGMA foreign_keys = ON;

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

CREATE TABLE AP_Payments (
    Payment_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    AP_Invoice_ID INTEGER NOT NULL REFERENCES AP_Invoices(AP_Invoice_ID),
    Payment_Date TEXT NOT NULL,
    Amount REAL NOT NULL,
    Method TEXT CHECK (Method IN ('CHECK','ACH','WIRE')),
    Check_Number TEXT
);

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

CREATE TABLE AR_Payments (
    Payment_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    AR_Invoice_ID INTEGER NOT NULL REFERENCES AR_Invoices(AR_Invoice_ID),
    Payment_Date TEXT NOT NULL,
    Amount REAL NOT NULL,
    Method TEXT CHECK (Method IN ('CHECK','ACH','WIRE','CREDIT_CARD','CASH')),
    Reference TEXT
);

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

CREATE TABLE BOM_Headers (
    BOM_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Item_ID INTEGER NOT NULL REFERENCES Items(Item_ID),
    BOM_Name TEXT NOT NULL,
    Revision TEXT DEFAULT 'A',
    Effective_Date TEXT,
    Status TEXT CHECK (Status IN ('ACTIVE','OBSOLETE','PENDING')),
    UNIQUE (Item_ID, Revision)
);

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

CREATE TABLE Departments (
    Dept_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Dept_Code TEXT UNIQUE NOT NULL,
    Dept_Name TEXT NOT NULL,
    Cost_Center TEXT,
    Manager_ID INTEGER REFERENCES Employees(Employee_ID),
    Active INTEGER DEFAULT 1
);

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

CREATE TABLE GL_Accounts (
    Account_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Account_Code TEXT NOT NULL UNIQUE,
    Account_Name TEXT NOT NULL,
    Account_Type TEXT NOT NULL CHECK (Account_Type IN ('ASSET','LIABILITY','EQUITY','REVENUE','EXPENSE')),
    Normal_Balance TEXT NOT NULL CHECK (Normal_Balance IN ('DEBIT','CREDIT')),
    Parent_ID INTEGER REFERENCES GL_Accounts(Account_ID),
    Active INTEGER DEFAULT 1
);

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

CREATE TABLE Price_Lists (
    Price_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Item_ID INTEGER NOT NULL REFERENCES Items(Item_ID),
    Customer_ID INTEGER REFERENCES Customers(Customer_ID),
    Price REAL NOT NULL,
    Min_Qty REAL DEFAULT 1,
    Effective_Date TEXT,
    Expiry_Date TEXT
);

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

CREATE TABLE Shipment_Lines (
    Ship_Line_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Shipment_ID INTEGER NOT NULL REFERENCES Shipments(Shipment_ID),
    SOLine_ID INTEGER NOT NULL REFERENCES SO_Lines(SOLine_ID),
    Qty_Shipped REAL NOT NULL
);

CREATE TABLE Shipments (
    Shipment_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    SO_ID INTEGER NOT NULL REFERENCES Sales_Orders(SO_ID),
    Ship_Date TEXT NOT NULL,
    Carrier TEXT,
    Tracking_No TEXT,
    Warehouse_ID INTEGER REFERENCES Warehouses(Warehouse_ID),
    Status TEXT CHECK (Status IN ('PACKED','SHIPPED','DELIVERED','RETURNED'))
);

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

CREATE TABLE WO_Materials (
    WO_Material_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    WO_ID INTEGER NOT NULL REFERENCES Work_Orders(WO_ID),
    Item_ID INTEGER NOT NULL REFERENCES Items(Item_ID),
    Qty_Required REAL NOT NULL,
    Qty_Issued REAL DEFAULT 0.00,
    Warehouse_ID INTEGER REFERENCES Warehouses(Warehouse_ID)
);

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

CREATE TABLE Warehouses (
    Warehouse_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Warehouse_Code TEXT UNIQUE NOT NULL,
    Warehouse_Name TEXT NOT NULL,
    Location TEXT,
    Manager_ID INTEGER REFERENCES Employees(Employee_ID)
);

CREATE TABLE Work_Centers (
    Center_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Center_Code TEXT UNIQUE NOT NULL,
    Center_Name TEXT NOT NULL,
    Department TEXT,
    Capacity_Hours_Day REAL DEFAULT 8.0,
    Hourly_Rate REAL DEFAULT 0.00,
    Status TEXT CHECK (Status IN ('ACTIVE','MAINTENANCE','OFFLINE'))
);

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

CREATE VIEW v_Reorder_Alert AS
SELECT *
FROM v_Available_Stock
WHERE Reorder_Point IS NOT NULL
  AND Available <= Reorder_Point;

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

