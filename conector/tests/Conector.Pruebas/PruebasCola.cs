using Conector.Nucleo;

namespace Conector.Pruebas;

public sealed class PruebasCola : IDisposable
{
    private readonly string _carpeta = Path.Combine(Path.GetTempPath(), "conector-pruebas-" + Guid.NewGuid());

    public void Dispose()
    {
        if (Directory.Exists(_carpeta))
            Directory.Delete(_carpeta, recursive: true);
    }

    [Fact]
    public async Task SinInternetGuardaLoPendienteYLoReenviaDespuesEnOrden()
    {
        var cola = new ColaPendientes(Path.Combine(_carpeta, "pendientes"));
        cola.Guardar(PruebasSeguridad.PaqueteDeEjemplo());
        cola.Guardar(PruebasSeguridad.PaqueteDeEjemplo() with { Desde = new DateOnly(2026, 6, 28), Hasta = new DateOnly(2026, 6, 29) });

        var sinInternet = new EnvioQueFalla();
        Assert.Equal(0, await cola.EnviarPendientesAsync(sinInternet));
        Assert.Equal(2, cola.Pendientes().Count);

        var conInternet = new EnvioQueApunta();
        Assert.Equal(2, await cola.EnviarPendientesAsync(conInternet));
        Assert.Empty(cola.Pendientes());
        Assert.Equal(2, conInternet.Recibidos.Count);
        Assert.Contains("20260627", conInternet.Recibidos[0]);
        Assert.Contains("20260628", conInternet.Recibidos[1]);
    }

    [Fact]
    public async Task SiFallaAMitadNoPierdeNada()
    {
        var cola = new ColaPendientes(Path.Combine(_carpeta, "pendientes"));
        cola.Guardar(PruebasSeguridad.PaqueteDeEjemplo());
        cola.Guardar(PruebasSeguridad.PaqueteDeEjemplo());
        cola.Guardar(PruebasSeguridad.PaqueteDeEjemplo());

        Assert.Equal(1, await cola.EnviarPendientesAsync(new EnvioQueFallaDesde(1)));
        Assert.Equal(2, cola.Pendientes().Count);
    }

    [Fact]
    public async Task ElEnvioSimuladoDejaElPaqueteEnUnaCarpeta()
    {
        var cola = new ColaPendientes(Path.Combine(_carpeta, "pendientes"));
        cola.Guardar(PruebasSeguridad.PaqueteDeEjemplo());
        var enviados = Path.Combine(_carpeta, "enviados");

        await cola.EnviarPendientesAsync(new EnvioSimuladoArchivo(enviados));

        Assert.Single(Directory.GetFiles(enviados, "*.json"));
    }

    private sealed class EnvioQueFalla : IEnvio
    {
        public Task EnviarAsync(string nombre, string json, CancellationToken ct = default) =>
            throw new HttpRequestException("Sin conexión");
    }

    private sealed class EnvioQueFallaDesde(int exitosos) : IEnvio
    {
        private int _llamadas;

        public Task EnviarAsync(string nombre, string json, CancellationToken ct = default) =>
            _llamadas++ < exitosos ? Task.CompletedTask : throw new HttpRequestException("Se cortó");
    }

    private sealed class EnvioQueApunta : IEnvio
    {
        public List<string> Recibidos { get; } = [];

        public Task EnviarAsync(string nombre, string json, CancellationToken ct = default)
        {
            Recibidos.Add(nombre);
            return Task.CompletedTask;
        }
    }
}
