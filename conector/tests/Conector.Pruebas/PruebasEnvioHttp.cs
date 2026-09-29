using System.Net;
using Conector.Adaptadores.DSTNet;
using Conector.Nucleo;

namespace Conector.Pruebas;

public sealed class PruebasEnvioHttp : IDisposable
{
    private readonly string _carpeta = Path.Combine(Path.GetTempPath(), "conector-http-" + Guid.NewGuid());

    public void Dispose()
    {
        if (Directory.Exists(_carpeta))
            Directory.Delete(_carpeta, recursive: true);
    }

    [Fact]
    public async Task EnviaConElTokenYSiElServidorFallaNoPierdeNada()
    {
        var servidor = new ServidorFalso(HttpStatusCode.ServiceUnavailable);
        var envio = new EnvioHttp(new HttpClient(servidor), new Uri("https://plataforma.ejemplo/"), "token-secreto");
        var cola = new ColaPendientes(_carpeta);
        cola.Guardar(PruebasSeguridad.PaqueteDeEjemplo());

        Assert.Equal(0, await cola.EnviarPendientesAsync(envio));
        Assert.Single(cola.Pendientes());

        servidor.Respuesta = HttpStatusCode.OK;
        Assert.Equal(1, await cola.EnviarPendientesAsync(envio));
        Assert.Empty(cola.Pendientes());
        Assert.Equal("https://plataforma.ejemplo/api/conector/v1/paquetes", servidor.UltimaUrl);
        Assert.Equal("Bearer token-secreto", servidor.UltimaAutorizacion);
    }

    // Prueba de extremo a extremo contra el servidor de verdad (servidor/): solo si se indica
    // CONECTOR_SERVIDOR_URL y CONECTOR_TOKEN, además de la copia de prueba de DSTNet.
    [SkippableFact]
    public async Task DeLaCajaALaPlataforma()
    {
        var url = Environment.GetEnvironmentVariable("CONECTOR_SERVIDOR_URL");
        var token = Environment.GetEnvironmentVariable("CONECTOR_TOKEN");
        var bd = Environment.GetEnvironmentVariable("CONECTOR_BD_PRUEBAS");
        Skip.If(string.IsNullOrWhiteSpace(url) || string.IsNullOrWhiteSpace(token) || string.IsNullOrWhiteSpace(bd),
            "Faltan CONECTOR_SERVIDOR_URL, CONECTOR_TOKEN o CONECTOR_BD_PRUEBAS.");

        var dia = new DateOnly(2026, 6, 27);
        var sincronizador = new Sincronizador(
            new AdaptadorDSTNet(bd!), new ColaPendientes(_carpeta), new EnvioHttp(new HttpClient(), new Uri(url!), token!));

        var resultado = await sincronizador.SincronizarAsync(dia, dia.AddDays(1));

        Assert.Equal(1, resultado.Enviados);
        Assert.Equal(0, resultado.Pendientes);
    }

    private sealed class ServidorFalso(HttpStatusCode respuesta) : HttpMessageHandler
    {
        public HttpStatusCode Respuesta { get; set; } = respuesta;
        public string? UltimaUrl { get; private set; }
        public string? UltimaAutorizacion { get; private set; }

        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage peticion, CancellationToken ct)
        {
            UltimaUrl = peticion.RequestUri?.ToString();
            UltimaAutorizacion = peticion.Headers.Authorization?.ToString();
            return Task.FromResult(new HttpResponseMessage(Respuesta));
        }
    }
}
