using Conector.Adaptadores.DSTNet;
using Conector.Nucleo;

namespace Conector.Pruebas;

// Pruebas que no necesitan base de datos.
public class PruebasSeguridad
{
    [Fact]
    public void TodasLasConsultasDelAdaptadorSonSoloDeLectura()
    {
        foreach (var sql in AdaptadorDSTNet.TodasLasConsultas)
            ConsultaSoloLectura.Validar(sql);
    }

    [Theory]
    [InlineData("INSERT INTO dbo.Article (Number) VALUES (1)")]
    [InlineData("UPDATE dbo.Article SET Description1 = 'x'")]
    [InlineData("DELETE FROM dbo.SalesOrderLine")]
    [InlineData("SELECT * INTO copia FROM dbo.SalesOrderLine")]
    [InlineData("SELECT 1; DROP TABLE dbo.Article")]
    [InlineData("SELECT 1 -- comentario")]
    [InlineData("EXEC sp_who")]
    [InlineData("  select 1 /* truco */ ")]
    public void RechazaCualquierConsultaQueNoSeaUnaLecturaSimple(string sql)
    {
        Assert.Throws<ConsultaNoPermitidaException>(() => ConsultaSoloLectura.Validar(sql));
    }

    [Fact]
    public void ElPaqueteDelIdiomaComunPasaElFiltro()
    {
        var json = System.Text.Json.JsonSerializer.Serialize(PaqueteDeEjemplo(), ColaPendientes.Json);
        FiltroCamposPermitidos.Validar(json);
    }

    [Theory]
    [InlineData("""{"tpv":"DSTNet","ventas":[{"localId":"1-1","employee":4}]}""")]
    [InlineData("""{"tpv":"DSTNet","nif":"12345678Z"}""")]
    [InlineData("""{"tpv":"DSTNet","tickets":[{"telePhone":"600000000"}]}""")]
    [InlineData("""{"tpv":"DSTNet","articulos":[{"id":"1","observation":"texto libre"}]}""")]
    public void BloqueaCualquierCampoQueNoEsteEnLaListaPermitida(string json)
    {
        Assert.Throws<CampoNoPermitidoException>(() => FiltroCamposPermitidos.Validar(json));
    }

    internal static PaqueteDatos PaqueteDeEjemplo() => new(
        "Prueba",
        new DateOnly(2026, 6, 27),
        new DateOnly(2026, 6, 28),
        DateTimeOffset.UnixEpoch,
        [new VentaHora("1-1", new DateOnly(2026, 6, 27), 12, "138", "CERVEZA", "10006", 2m, 3m)],
        [new TicketsHora("1-1", new DateOnly(2026, 6, 27), 12, 1, 2)],
        [new Familia("10006", "CERVEZAS NACIONALES", "1", "BEBIDAS")],
        [new Articulo("138", "CERVEZA", "10006", true)],
        [new PrecioArticulo("138", "0", 1.5m)]);
}
