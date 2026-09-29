using System.Text.Json;

namespace Conector.Nucleo;

/// <summary>
/// Última barrera antes de enviar nada: el paquete ya convertido a JSON solo puede contener
/// los campos de esta lista. Si aparece cualquier otro (por ejemplo "Employee" o "Nif"),
/// no se envía.
/// </summary>
public static class FiltroCamposPermitidos
{
    public static readonly IReadOnlySet<string> Permitidos = new HashSet<string>(StringComparer.Ordinal)
    {
        // PaqueteDatos
        "tpv", "desde", "hasta", "generadoEn", "ventas", "tickets", "familias", "articulos", "precios",
        // VentaHora
        "localId", "fecha", "hora", "articuloId", "articuloNombre", "familiaId", "unidades", "importe",
        // TicketsHora ("tickets" ya está arriba)
        "comensales",
        // Familia
        "id", "nombre", "familiaPrincipalId", "familiaPrincipalNombre",
        // Articulo
        "seVende",
        // PrecioArticulo
        "tarifaId", "precio",
    };

    /// <summary>Lanza una excepción si el JSON contiene algún campo fuera de la lista permitida.</summary>
    public static void Validar(string json)
    {
        using var documento = JsonDocument.Parse(json);
        Revisar(documento.RootElement, "$");
    }

    private static void Revisar(JsonElement elemento, string ruta)
    {
        switch (elemento.ValueKind)
        {
            case JsonValueKind.Object:
                foreach (var campo in elemento.EnumerateObject())
                {
                    if (!Permitidos.Contains(campo.Name))
                        throw new CampoNoPermitidoException($"Campo no permitido «{campo.Name}» en {ruta}.");
                    Revisar(campo.Value, $"{ruta}.{campo.Name}");
                }
                break;
            case JsonValueKind.Array:
                var i = 0;
                foreach (var hijo in elemento.EnumerateArray())
                    Revisar(hijo, $"{ruta}[{i++}]");
                break;
        }
    }
}

public sealed class CampoNoPermitidoException(string mensaje) : Exception(mensaje);
