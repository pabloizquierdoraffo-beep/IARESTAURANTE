using System.Text.Json;
using Conector.Adaptadores.DSTNet;
using Conector.Nucleo;
using Microsoft.Data.SqlClient;

namespace Conector.Pruebas;

// Pruebas contra la copia de prueba de DSTNet (1 día de ventas: 27/06/2026).
// Necesitan la variable CONECTOR_BD_PRUEBAS con la conexión del usuario de SOLO LECTURA
// (ver pruebas/preparar-bd-pruebas.sh). Sin ella, se saltan.
public class PruebasDSTNet
{
    private static readonly string? Conexion = Environment.GetEnvironmentVariable("CONECTOR_BD_PRUEBAS");
    private static readonly DateOnly Dia = new(2026, 6, 27);

    private static async Task<PaqueteDatos> LeerDiaDePrueba()
    {
        Skip.If(string.IsNullOrWhiteSpace(Conexion), "Falta CONECTOR_BD_PRUEBAS: no hay copia de prueba cargada.");
        return await new AdaptadorDSTNet(Conexion!).LeerAsync(Dia, Dia.AddDays(1));
    }

    [SkippableFact]
    public async Task LosTotalesCuadranConLaCopiaDePrueba()
    {
        var paquete = await LeerDiaDePrueba();

        Assert.Equal(84.50m, paquete.Ventas.Sum(v => v.Importe));
        Assert.Equal(50m, paquete.Ventas.Sum(v => v.Unidades));
        Assert.Equal(27, paquete.Tickets.Sum(t => t.Tickets));
        Assert.Equal(27, paquete.Tickets.Sum(t => t.Comensales));
        Assert.All(paquete.Ventas, v => Assert.Equal("1-1", v.LocalId));
        Assert.All(paquete.Ventas, v => Assert.Equal(Dia, v.Fecha));
    }

    [SkippableFact]
    public async Task ReparteLasVentasPorHora()
    {
        var paquete = await LeerDiaDePrueba();
        var porHora = paquete.Ventas.GroupBy(v => v.Hora).ToDictionary(g => g.Key, g => g.Sum(v => v.Importe));

        Assert.Equal(new[] { 9, 10, 11, 12 }, porHora.Keys.Order());
        Assert.Equal(1.5m, porHora[9]);
        Assert.Equal(6m, porHora[10]);
        Assert.Equal(27.5m, porHora[11]);
        Assert.Equal(49.5m, porHora[12]);
    }

    [SkippableFact]
    public async Task TraeLaCartaYLasFamilias()
    {
        var paquete = await LeerDiaDePrueba();

        Assert.Equal(59, paquete.Familias.Count);
        Assert.Equal(148, paquete.Articulos.Count);
        Assert.Equal(91, paquete.Precios.Count);
        var cervezas = paquete.Familias.Single(f => f.Id == "10006");
        Assert.Equal("CERVEZAS NACIONALES", cervezas.Nombre);
        Assert.Equal("BEBIDAS", cervezas.FamiliaPrincipalNombre);
    }

    [SkippableFact]
    public async Task NoSaleNingunDatoPersonal()
    {
        var paquete = await LeerDiaDePrueba();
        var json = JsonSerializer.Serialize(paquete, ColaPendientes.Json);

        FiltroCamposPermitidos.Validar(json);
        foreach (var prohibido in new[] { "employee", "nif", "telePhone", "teleName", "webFullName", "observation", "customerNumber" })
            Assert.DoesNotContain($"\"{prohibido}\"", json, StringComparison.OrdinalIgnoreCase);
    }

    [SkippableFact]
    public async Task ElUsuarioDelConectorNoPuedeEscribirEnElTpv()
    {
        Skip.If(string.IsNullOrWhiteSpace(Conexion), "Falta CONECTOR_BD_PRUEBAS: no hay copia de prueba cargada.");
        await using var conexion = new SqlConnection(Conexion);
        await conexion.OpenAsync();

        // Se salta a propósito la barrera ConsultaSoloLectura para comprobar la otra: los permisos.
        foreach (var sql in new[]
                 {
                     "UPDATE dbo.Article SET Description1 = Description1 WHERE Number = 1",
                     "DELETE FROM dbo.SalesOrderLine WHERE 1 = 0",
                     "INSERT INTO dbo.Tariff (Number, Description) VALUES (-1, 'x')",
                 })
        {
            await using var comando = new SqlCommand(sql, conexion);
            var error = await Assert.ThrowsAsync<SqlException>(() => comando.ExecuteNonQueryAsync());
            Assert.Contains("permission", error.Message, StringComparison.OrdinalIgnoreCase);
        }
    }

    [SkippableFact]
    public async Task SincronizaDeExtremoAExtremo()
    {
        Skip.If(string.IsNullOrWhiteSpace(Conexion), "Falta CONECTOR_BD_PRUEBAS: no hay copia de prueba cargada.");
        var carpeta = Path.Combine(Path.GetTempPath(), "conector-e2e-" + Guid.NewGuid());
        try
        {
            var sincronizador = new Sincronizador(
                new AdaptadorDSTNet(Conexion!),
                new ColaPendientes(Path.Combine(carpeta, "pendientes")),
                new EnvioSimuladoArchivo(Path.Combine(carpeta, "enviados")));

            var resultado = await sincronizador.SincronizarAsync(Dia, Dia.AddDays(1));

            Assert.Equal(1, resultado.Enviados);
            Assert.Equal(0, resultado.Pendientes);
            var enviado = await File.ReadAllTextAsync(Directory.GetFiles(Path.Combine(carpeta, "enviados")).Single());
            var paquete = JsonSerializer.Deserialize<PaqueteDatos>(enviado, ColaPendientes.Json)!;
            Assert.Equal(84.50m, paquete.Ventas.Sum(v => v.Importe));
        }
        finally
        {
            Directory.Delete(carpeta, recursive: true);
        }
    }
}
