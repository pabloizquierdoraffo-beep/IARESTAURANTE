namespace Conector.Nucleo;

// El "idioma común": el único formato en el que cualquier adaptador de TPV entrega los datos.
// Todo va agrupado por local, día y hora. Aquí no cabe ningún dato personal: si hiciera falta
// un campo nuevo, hay que añadirlo aquí Y en FiltroCamposPermitidos, a propósito.

/// <summary>Ventas de un artículo en un local, un día y una hora concretos.</summary>
public sealed record VentaHora(
    string LocalId,
    DateOnly Fecha,
    int Hora,
    string ArticuloId,
    string ArticuloNombre,
    string? FamiliaId,
    decimal Unidades,
    decimal Importe);

/// <summary>Número de tickets y de comensales de un local en un día y una hora.</summary>
public sealed record TicketsHora(
    string LocalId,
    DateOnly Fecha,
    int Hora,
    int Tickets,
    int Comensales);

/// <summary>Familia de productos (por ejemplo "CERVEZAS NACIONALES") y su familia principal ("BEBIDAS").</summary>
public sealed record Familia(
    string Id,
    string Nombre,
    string? FamiliaPrincipalId,
    string? FamiliaPrincipalNombre);

/// <summary>Artículo de la carta.</summary>
public sealed record Articulo(
    string Id,
    string Nombre,
    string? FamiliaId,
    bool SeVende);

/// <summary>Precio de un artículo en una tarifa del TPV.</summary>
public sealed record PrecioArticulo(
    string ArticuloId,
    string TarifaId,
    decimal Precio);

/// <summary>Todo lo que se envía en una sincronización.</summary>
public sealed record PaqueteDatos(
    string Tpv,
    DateOnly Desde,
    DateOnly Hasta,
    DateTimeOffset GeneradoEn,
    IReadOnlyList<VentaHora> Ventas,
    IReadOnlyList<TicketsHora> Tickets,
    IReadOnlyList<Familia> Familias,
    IReadOnlyList<Articulo> Articulos,
    IReadOnlyList<PrecioArticulo> Precios);
