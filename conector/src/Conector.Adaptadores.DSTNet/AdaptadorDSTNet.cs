using Conector.Nucleo;
using Microsoft.Data.SqlClient;

namespace Conector.Adaptadores.DSTNet;

/// <summary>
/// Traductor de DSTNet (base de datos "Central", SQL Server) al idioma común.
///
/// Solo lee, y solo estas columnas. Nunca lee empleados, clientes, textos libres, pagos ni
/// datos fiscales (ver docs/mapa-datos-tpv.md). Debe usarse con un usuario de base de datos
/// de solo lectura; además, cada consulta pasa por ConsultaSoloLectura antes de ejecutarse.
///
/// Pendiente de confirmar con el fabricante: el significado de LineType, menús y tarifas.
/// Por ahora se cuentan todas las líneas de SalesOrderLine tal cual.
/// </summary>
public sealed class AdaptadorDSTNet(string cadenaConexion) : IAdaptadorTpv
{
    public string Tpv => "DSTNet";

    // El local se identifica como "Empresa-Establecimiento".
    internal const string ConsultaVentas = """
        SELECT CAST(l.Company AS varchar(12)) + '-' + CAST(l.Establishment AS varchar(12)) AS LocalId,
               CAST(l.OrderDate AS date) AS Fecha,
               DATEPART(hour, l.OrderDate) AS Hora,
               CAST(l.Article AS varchar(12)) AS ArticuloId,
               ISNULL(l.Description, '') AS ArticuloNombre,
               CAST(l.TurnOverGroup AS varchar(12)) AS FamiliaId,
               SUM(l.Amount) AS Unidades,
               SUM(l.Price * l.Amount) AS Importe
        FROM dbo.SalesOrderLine AS l
        WHERE l.OrderDate >= @desde AND l.OrderDate < @hasta
        GROUP BY l.Company, l.Establishment, CAST(l.OrderDate AS date), DATEPART(hour, l.OrderDate),
                 l.Article, l.Description, l.TurnOverGroup
        ORDER BY Fecha, Hora, LocalId, ArticuloId, ArticuloNombre
        """;

    internal const string ConsultaTickets = """
        SELECT CAST(o.Company AS varchar(12)) + '-' + CAST(o.Establishment AS varchar(12)) AS LocalId,
               CAST(o.OrderDate AS date) AS Fecha,
               DATEPART(hour, o.OrderDate) AS Hora,
               COUNT(*) AS Tickets,
               SUM(ISNULL(o.TableMembers, 0)) AS Comensales
        FROM dbo.SalesOrder AS o
        WHERE o.OrderDate >= @desde AND o.OrderDate < @hasta
        GROUP BY o.Company, o.Establishment, CAST(o.OrderDate AS date), DATEPART(hour, o.OrderDate)
        ORDER BY Fecha, Hora, LocalId
        """;

    internal const string ConsultaFamilias = """
        SELECT CAST(t.Number AS varchar(12)) AS Id,
               ISNULL(t.Description, '') AS Nombre,
               CAST(m.Number AS varchar(12)) AS FamiliaPrincipalId,
               m.Description AS FamiliaPrincipalNombre
        FROM dbo.TurnOverGroup AS t
        LEFT JOIN dbo.MainTurnOverGroup AS m ON m.Number = t.MainTurnOverGroup
        ORDER BY t.Number
        """;

    internal const string ConsultaArticulos = """
        SELECT CAST(a.Number AS varchar(12)) AS Id,
               ISNULL(a.Description, '') AS Nombre,
               CAST(a.TurnOverGroup AS varchar(12)) AS FamiliaId,
               CAST(ISNULL(a.CanSell, 0) AS bit) AS SeVende
        FROM dbo.ArticleHeader AS a
        ORDER BY a.Number
        """;

    internal const string ConsultaPrecios = """
        SELECT CAST(p.Article AS varchar(12)) AS ArticuloId,
               CAST(p.Tariff AS varchar(12)) AS TarifaId,
               p.Price AS Precio
        FROM dbo.ArticleTariff AS p
        WHERE p.Price IS NOT NULL
        ORDER BY p.Article, p.Tariff
        """;

    internal static readonly string[] TodasLasConsultas =
        [ConsultaVentas, ConsultaTickets, ConsultaFamilias, ConsultaArticulos, ConsultaPrecios];

    public async Task<PaqueteDatos> LeerAsync(DateOnly desde, DateOnly hasta, CancellationToken ct = default)
    {
        if (hasta <= desde)
            throw new ArgumentException("La fecha final debe ser posterior a la inicial.", nameof(hasta));

        await using var conexion = new SqlConnection(cadenaConexion);
        await conexion.OpenAsync(ct);

        var inicio = desde.ToDateTime(TimeOnly.MinValue);
        var fin = hasta.ToDateTime(TimeOnly.MinValue);

        var ventas = await LeerAsync(conexion, ConsultaVentas, inicio, fin, l => new VentaHora(
            l.GetString(0), DateOnly.FromDateTime(l.GetDateTime(1)), l.GetInt32(2), l.GetString(3), l.GetString(4),
            l.IsDBNull(5) ? null : l.GetString(5), l.GetDecimal(6), l.GetDecimal(7)), ct);

        var tickets = await LeerAsync(conexion, ConsultaTickets, inicio, fin, l => new TicketsHora(
            l.GetString(0), DateOnly.FromDateTime(l.GetDateTime(1)), l.GetInt32(2), l.GetInt32(3), l.GetInt32(4)), ct);

        var familias = await LeerAsync(conexion, ConsultaFamilias, null, null, l => new Familia(
            l.GetString(0), l.GetString(1), l.IsDBNull(2) ? null : l.GetString(2), l.IsDBNull(3) ? null : l.GetString(3)), ct);

        var articulos = await LeerAsync(conexion, ConsultaArticulos, null, null, l => new Articulo(
            l.GetString(0), l.GetString(1), l.IsDBNull(2) ? null : l.GetString(2), l.GetBoolean(3)), ct);

        var precios = await LeerAsync(conexion, ConsultaPrecios, null, null, l => new PrecioArticulo(
            l.GetString(0), l.GetString(1), l.GetDecimal(2)), ct);

        return new PaqueteDatos(Tpv, desde, hasta, DateTimeOffset.UtcNow, ventas, tickets, familias, articulos, precios);
    }

    private static async Task<List<T>> LeerAsync<T>(
        SqlConnection conexion, string sql, DateTime? desde, DateTime? hasta,
        Func<SqlDataReader, T> convertir, CancellationToken ct)
    {
        ConsultaSoloLectura.Validar(sql);

        await using var comando = new SqlCommand(sql, conexion) { CommandTimeout = 120 };
        if (desde is not null)
        {
            comando.Parameters.Add("@desde", System.Data.SqlDbType.DateTime).Value = desde.Value;
            comando.Parameters.Add("@hasta", System.Data.SqlDbType.DateTime).Value = hasta!.Value;
        }

        var resultado = new List<T>();
        await using var lector = await comando.ExecuteReaderAsync(ct);
        while (await lector.ReadAsync(ct))
            resultado.Add(convertir(lector));
        return resultado;
    }
}
