# SE-Doorbell-Camera

Câmara na campainha 🕭🎦

Este projeto será para colocar uma câmara na porta de uma casa/apartamento.

A câmara deve ser ativada caso se carregar na campainha ou se detetar movimento. Nestes casos as imagens devem ser gravadas com "stop-motion", i.e., com várias fotos em vez de filme de modo a poupar espaço. O sistema pára passados 5 minutos depois de deixar de detetar alguém.

Ao tocar a campainha o utilizador deve ser notificado no seu smartphone. Neste caso ele pode pedir um stream de vídeo sem ser o "stop-motion". No smartphone deve ser possível ver os "stop-motions" gravados e apagar os mesmos. Também deve ser possível acionar a câmara para ver o streaming.

Deve haver uma luz vermelha a indicar que a câmara está a gravar.


Requisitos

    detecção de presença na porta deve ser inferior a 3 seg;
    início de gravação desde deteção ou toque na campainha deve ser inferior a 3 seg;
    pedido de stream de video do smartphone deve ter um atraso inferior a 10 seg
    presença deve ser detetada no mínimo a 50 cm
