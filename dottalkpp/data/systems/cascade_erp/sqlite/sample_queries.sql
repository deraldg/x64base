-- Cascade Precision Mfg ERP Phase 2 sample queries

PRAGMA foreign_keys = ON;

SELECT count(*) AS user_tables
FROM sqlite_schema
WHERE type='table' AND name NOT LIKE 'sqlite_%';

SELECT count(*) AS analytical_views
FROM sqlite_schema
WHERE type='view';

SELECT SUM(row_count) AS sample_records
FROM (
    SELECT count(*) AS row_count FROM GL_Accounts UNION ALL
    SELECT count(*) FROM GL_Journal UNION ALL
    SELECT count(*) FROM AP_Invoices UNION ALL
    SELECT count(*) FROM AP_Payments UNION ALL
    SELECT count(*) FROM AR_Invoices UNION ALL
    SELECT count(*) FROM AR_Payments UNION ALL
    SELECT count(*) FROM Items UNION ALL
    SELECT count(*) FROM Warehouses UNION ALL
    SELECT count(*) FROM Stock_Levels UNION ALL
    SELECT count(*) FROM Inventory_Movements UNION ALL
    SELECT count(*) FROM Work_Centers UNION ALL
    SELECT count(*) FROM BOM_Headers UNION ALL
    SELECT count(*) FROM BOM_Details UNION ALL
    SELECT count(*) FROM Routings UNION ALL
    SELECT count(*) FROM Work_Orders UNION ALL
    SELECT count(*) FROM WO_Materials UNION ALL
    SELECT count(*) FROM WO_Operations UNION ALL
    SELECT count(*) FROM Vendors UNION ALL
    SELECT count(*) FROM Vendor_Items UNION ALL
    SELECT count(*) FROM Purchase_Orders UNION ALL
    SELECT count(*) FROM PO_Lines UNION ALL
    SELECT count(*) FROM Receiving UNION ALL
    SELECT count(*) FROM Departments UNION ALL
    SELECT count(*) FROM Employees UNION ALL
    SELECT count(*) FROM Time_Cards UNION ALL
    SELECT count(*) FROM Payroll_Runs UNION ALL
    SELECT count(*) FROM Customers UNION ALL
    SELECT count(*) FROM Price_Lists UNION ALL
    SELECT count(*) FROM Sales_Orders UNION ALL
    SELECT count(*) FROM SO_Lines UNION ALL
    SELECT count(*) FROM Shipments UNION ALL
    SELECT count(*) FROM Shipment_Lines UNION ALL
    SELECT count(*) FROM Quality_Tests UNION ALL
    SELECT count(*) FROM Quality_Results
);

SELECT * FROM v_Reorder_Alert ORDER BY SKU, Warehouse_Code;
SELECT * FROM v_Open_Sales_Orders ORDER BY Required_Date;
SELECT * FROM v_Work_Order_Status ORDER BY Due_Date, WO_Number;
SELECT * FROM v_BOM_Explosion WHERE Parent_SKU='PDU-100' ORDER BY Sequence;
SELECT * FROM v_Three_Way_Match ORDER BY PO_Number;
SELECT * FROM v_Trial_Balance ORDER BY Account_Code;
SELECT ROUND(SUM(Total_Debit),2) AS total_debit, ROUND(SUM(Total_Credit),2) AS total_credit FROM v_Trial_Balance;
