CREATE DATABASE MPS_SupplyChain;
GO
USE MPS_SupplyChain;
GO
CREATE TABLE dbo.Productos(SKU VARCHAR(20) PRIMARY KEY, Referencia VARCHAR(150), Marca VARCHAR(50), Categoria VARCHAR(80), TipoProducto VARCHAR(60), CostoUnitarioCOP BIGINT, PrecioListaCOP BIGINT, EstadoReferencia VARCHAR(30));
CREATE TABLE dbo.Proveedores(ProveedorID VARCHAR(20) PRIMARY KEY, Proveedor VARCHAR(100), PaisOrigen VARCHAR(50), TiempoEntregaPromedioDias INT, EstadoProveedor VARCHAR(30));
CREATE TABLE dbo.Ventas(VentaID VARCHAR(20) PRIMARY KEY, FechaVenta DATE, SKU VARCHAR(20) FOREIGN KEY REFERENCES dbo.Productos(SKU), Cantidad INT, PrecioUnitarioCOP DECIMAL(18,2), DescuentoPct DECIMAL(5,2), ValorVentaCOP DECIMAL(18,2), Canal VARCHAR(50), Ciudad VARCHAR(50));
CREATE TABLE dbo.Inventario(FechaCorte DATE, SKU VARCHAR(20) FOREIGN KEY REFERENCES dbo.Productos(SKU), StockUnidades INT, CostoInventarioCOP BIGINT, StockReservado INT, PRIMARY KEY(FechaCorte,SKU));
CREATE TABLE dbo.Importaciones(OrdenImportacionID VARCHAR(20) PRIMARY KEY, SKU VARCHAR(20) FOREIGN KEY REFERENCES dbo.Productos(SKU), ProveedorID VARCHAR(20) FOREIGN KEY REFERENCES dbo.Proveedores(ProveedorID), FechaPedido DATE, FechaEntregaEsperada DATE, FechaRecepcion DATE NULL, CantidadOrdenada INT, CostoUnitarioImportacionCOP BIGINT, EstadoImportacion VARCHAR(30));
CREATE TABLE dbo.Calendario(Fecha DATE PRIMARY KEY, Año SMALLINT, MesNumero TINYINT, Mes VARCHAR(20), Trimestre VARCHAR(5), AñoMes CHAR(7), DiaSemana VARCHAR(20));
GO
-- Ejecuta estas consultas después de importar las hojas:
SELECT COUNT(*) AS Productos FROM dbo.Productos;
SELECT COUNT(*) AS Ventas FROM dbo.Ventas;
SELECT COUNT(*) AS CortesInventario FROM dbo.Inventario;
SELECT COUNT(*) AS Importaciones FROM dbo.Importaciones;
SELECT YEAR(FechaVenta) AS Año, MONTH(FechaVenta) AS Mes, SUM(Cantidad) AS Unidades, SUM(ValorVentaCOP) AS VentasCOP FROM dbo.Ventas GROUP BY YEAR(FechaVenta),MONTH(FechaVenta) ORDER BY Año,Mes;
