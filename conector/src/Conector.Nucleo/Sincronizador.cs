namespace Conector.Nucleo;

/// <summary>Une las piezas: leer del TPV, guardar en la cola y enviar lo pendiente.</summary>
public sealed class Sincronizador(IAdaptadorTpv adaptador, ColaPendientes cola, IEnvio envio)
{
    public async Task<ResultadoSincronizacion> SincronizarAsync(DateOnly desde, DateOnly hasta, CancellationToken ct = default)
    {
        var paquete = await adaptador.LeerAsync(desde, hasta, ct);
        cola.Guardar(paquete);
        var enviados = await cola.EnviarPendientesAsync(envio, ct);
        return new ResultadoSincronizacion(enviados, cola.Pendientes().Count);
    }
}

public sealed record ResultadoSincronizacion(int Enviados, int Pendientes);
