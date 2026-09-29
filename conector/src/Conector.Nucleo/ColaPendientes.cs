using System.Text.Json;

namespace Conector.Nucleo;

/// <summary>Destino de los envíos (el servidor; de momento, uno simulado).</summary>
public interface IEnvio
{
    Task EnviarAsync(string nombre, string json, CancellationToken ct = default);
}

/// <summary>
/// Guarda en disco lo que hay que enviar y lo envía cuando se puede. Si no hay internet,
/// los paquetes se quedan en la carpeta y se reenvían en el siguiente intento, en orden.
/// </summary>
public sealed class ColaPendientes
{
    public static readonly JsonSerializerOptions Json = new(JsonSerializerDefaults.Web);

    private readonly string _carpeta;

    public ColaPendientes(string carpeta)
    {
        _carpeta = carpeta;
        Directory.CreateDirectory(_carpeta);
    }

    public IReadOnlyList<string> Pendientes() =>
        Directory.GetFiles(_carpeta, "*.json").Order(StringComparer.Ordinal).ToList();

    /// <summary>Comprueba el paquete con el filtro de campos y lo deja guardado para enviar.</summary>
    public string Guardar(PaqueteDatos paquete)
    {
        var json = JsonSerializer.Serialize(paquete, Json);
        FiltroCamposPermitidos.Validar(json);

        var nombre = $"{DateTimeOffset.UtcNow:yyyyMMddHHmmssfffffff}-{paquete.Tpv}-{paquete.Desde:yyyyMMdd}-{paquete.Hasta:yyyyMMdd}.json";
        var destino = Path.Combine(_carpeta, nombre);
        // Se escribe en un temporal y luego se renombra, para no dejar nunca un archivo a medias.
        var temporal = destino + ".tmp";
        File.WriteAllText(temporal, json);
        File.Move(temporal, destino);
        return destino;
    }

    /// <summary>
    /// Envía los pendientes en orden. Se para en el primer fallo y deja el resto para después.
    /// Devuelve cuántos se enviaron.
    /// </summary>
    public async Task<int> EnviarPendientesAsync(IEnvio envio, CancellationToken ct = default)
    {
        var enviados = 0;
        foreach (var archivo in Pendientes())
        {
            var json = await File.ReadAllTextAsync(archivo, ct);
            try
            {
                await envio.EnviarAsync(Path.GetFileName(archivo), json, ct);
            }
            catch (Exception) when (!ct.IsCancellationRequested)
            {
                break;
            }
            File.Delete(archivo);
            enviados++;
        }
        return enviados;
    }
}

/// <summary>Envío simulado: copia los paquetes a una carpeta. Se usará hasta que exista el servidor.</summary>
public sealed class EnvioSimuladoArchivo(string carpeta) : IEnvio
{
    public async Task EnviarAsync(string nombre, string json, CancellationToken ct = default)
    {
        Directory.CreateDirectory(carpeta);
        await File.WriteAllTextAsync(Path.Combine(carpeta, nombre), json, ct);
    }
}

/// <summary>
/// Envío real a la plataforma, cifrado (https) y con el token del conector.
/// Si el servidor no contesta bien, lanza una excepción y el paquete se queda en la cola.
/// </summary>
public sealed class EnvioHttp(HttpClient http, Uri servidor, string token) : IEnvio
{
    public async Task EnviarAsync(string nombre, string json, CancellationToken ct = default)
    {
        using var peticion = new HttpRequestMessage(HttpMethod.Post, new Uri(servidor, "api/conector/v1/paquetes"))
        {
            Content = new StringContent(json, System.Text.Encoding.UTF8, "application/json"),
        };
        peticion.Headers.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", token);
        using var respuesta = await http.SendAsync(peticion, ct);
        if (!respuesta.IsSuccessStatusCode)
        {
            var detalle = await respuesta.Content.ReadAsStringAsync(ct);
            throw new HttpRequestException($"El servidor rechazó el paquete ({(int)respuesta.StatusCode}): {detalle}");
        }
    }
}
