namespace Conector.Nucleo;

/// <summary>
/// Traductor de un programa de caja (TPV) al idioma común.
/// Cada TPV tiene el suyo. Solo puede LEER: nunca escribe en el TPV.
/// </summary>
public interface IAdaptadorTpv
{
    /// <summary>Nombre del TPV, por ejemplo "DSTNet".</summary>
    string Tpv { get; }

    /// <summary>Lee los datos entre <paramref name="desde"/> (incluido) y <paramref name="hasta"/> (excluido).</summary>
    Task<PaqueteDatos> LeerAsync(DateOnly desde, DateOnly hasta, CancellationToken ct = default);
}
