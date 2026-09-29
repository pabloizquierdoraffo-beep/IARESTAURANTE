using System.Text.RegularExpressions;

namespace Conector.Nucleo;

/// <summary>
/// Segunda barrera para no escribir nunca en el TPV (la primera es usar un usuario de base de
/// datos de solo lectura). Rechaza cualquier consulta que no sea una lectura simple.
/// </summary>
public static partial class ConsultaSoloLectura
{
    [GeneratedRegex(
        @"\b(INSERT|UPDATE|DELETE|MERGE|DROP|ALTER|CREATE|TRUNCATE|EXEC|EXECUTE|GRANT|REVOKE|DENY|BACKUP|RESTORE|INTO|OPENROWSET|OPENQUERY|OPENDATASOURCE|DBCC|SHUTDOWN|KILL|RECONFIGURE)\b",
        RegexOptions.IgnoreCase | RegexOptions.CultureInvariant)]
    private static partial Regex PalabrasProhibidas();

    [GeneratedRegex(@"--|/\*|;", RegexOptions.CultureInvariant)]
    private static partial Regex ComentariosOVarias();

    /// <summary>Lanza una excepción si la consulta no es una lectura (SELECT) simple.</summary>
    public static void Validar(string sql)
    {
        var texto = sql.Trim();
        if (!texto.StartsWith("SELECT", StringComparison.OrdinalIgnoreCase))
            throw new ConsultaNoPermitidaException("Solo se permiten consultas que empiezan por SELECT.");
        if (ComentariosOVarias().IsMatch(texto))
            throw new ConsultaNoPermitidaException("No se permiten comentarios ni varias instrucciones en una consulta.");
        var prohibida = PalabrasProhibidas().Match(texto);
        if (prohibida.Success)
            throw new ConsultaNoPermitidaException($"La consulta contiene una palabra no permitida: {prohibida.Value}.");
    }
}

public sealed class ConsultaNoPermitidaException(string mensaje) : Exception(mensaje);
