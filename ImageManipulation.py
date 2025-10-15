import numpy as np
from PIL import Image
import matplotlib.pyplot as plt


class ImageManipulation():
    def __init__(self, caminho_imagem):
        self.caminho_imagem = caminho_imagem
        self.imagem_original = self.extrair_pixels_rgb()
        self.imagem_manipulada = self.imagem_original.copy()
        self.altura, self.largura, self.canais = self.imagem_original.shape

    def extrair_pixels_rgb(self):
        if self.caminho_imagem is None:
            raise ValueError("Nenhum caminho de imagem fornecido.")

        with Image.open(self.caminho_imagem) as img:
            img = img.convert('RGB')
            pixels = np.array(img, dtype=np.uint8)
        return pixels

    def exibir_imagem_original(self, titulo="Imagem"):
        plt.figure(figsize=(10, 8))
        plt.imshow(self.imagem_original)
        plt.title(titulo)
        plt.axis('off')
        plt.tight_layout()
        plt.show()
    
    def exibir_imagem_manipulada(self, titulo="Imagem"):
        plt.figure(figsize=(10, 8))
        plt.imshow(self.imagem_manipulada)
        plt.title(titulo)
        plt.axis('off')
        plt.tight_layout()
        plt.show()

    def salvar_imagem_manipulada(self, caminho_saida):
        img = Image.fromarray(self.imagem_manipulada, 'RGB')
        img.save(caminho_saida)

    @staticmethod
    def ativacao_relu(x):
        return np.maximum(0, x)

    @staticmethod
    def ativacao_identidade(x):
        return x

    def ler_filtro(self, arquivo):
        """Lê um arquivo de filtro e retorna (mascara, bias, ativacao).

        Formato esperado do arquivo (exemplo):
            mascara:
            0 1 0
            1 -4 1
            0 1 0
            bias: 0
            ativacao: relu
        """
        mascara = []
        bias = 0.0
        ativacao = 'identidade'

        with open(arquivo, 'r', encoding='utf-8') as f:
            linhas = f.readlines()

        parsing_mascara = False
        for linha in linhas:
            texto = linha.strip()
            if not texto:
                continue
            if texto.lower().startswith('mascara:'):
                parsing_mascara = True
                continue
            if texto.lower().startswith('bias:'):
                parsing_mascara = False
                try:
                    bias = float(texto.split(':', 1)[1].strip())
                except Exception:
                    bias = 0.0
                continue
            if texto.lower().startswith('ativacao:'):
                parsing_mascara = False
                ativacao = texto.split(':', 1)[1].strip().lower()
                continue

            partes = texto.split()
            try:
                numeros = [float(x) for x in partes]
                mascara.append(numeros)
            except ValueError:
                continue

        if len(mascara) == 0:
            raise ValueError(f"Nenhuma máscara encontrada em {arquivo}")

        mascara_arr = np.array(mascara, dtype=float)
        return mascara_arr, bias, ativacao

    def correlacao_manual(self, imagem, mascara, bias=0.0, ativacao='identidade', clip=False):
        """
        Aplica correlação 2D manualmente (por canal) entre a imagem e a máscara.

        - imagem: array HxWxC
        - mascara: array mxn
        - bias: valor adicionado
        - ativacao: 'relu' ou 'identidade'
        - clip: se True, limita os valores a [0,255] e retorna uint8
        """
        linhas, colunas, canais = imagem.shape
        m, n = mascara.shape
        resultado = np.zeros_like(imagem, dtype=np.int32)

        # percorre por canal
        for canal in range(canais):
            for i in range(linhas - m + 1):
                for j in range(colunas - n + 1):
                    regiao = imagem[i:i+m, j:j+n, canal]
                    valor = np.sum(regiao * mascara) + bias
                    if ativacao == 'relu':
                        valor_ativado = self.ativacao_relu(valor)
                    else:
                        valor_ativado = self.ativacao_identidade(valor)
                    resultado[i, j, canal] = int(valor_ativado)

        if clip:
            resultado = np.clip(resultado, 0, 255).astype(np.uint8)
            return resultado
        return resultado

    @staticmethod
    def visualizar_sobel(img_sobel):
        """
        Gera uma versão visualizável (uint8) a partir de uma imagem Sobel que
        pode conter valores negativos/positivos.
        """
        img_abs = np.abs(img_sobel)
        r_min = np.min(img_abs)
        r_max = np.max(img_abs)

        if r_max > r_min:
            img_expandida = ((img_abs - r_min) / (r_max - r_min) * 255)
        else:
            img_expandida = img_abs

        return img_expandida.astype(np.uint8)

    def equalizacao_local(self, imagem=None, m=50, n=50):
        """
        Equalização local com janelas m×n:
        Para cada pixel e canal, calcula o histograma da vizinhança e aplica
        a transformação apenas no pixel central.
        """
        # aceitar imagem opcional (compatibilidade com chamadas que passam imagem)
        if imagem is None:
            img = np.asarray(self.imagem_original)
        else:
            img = np.asarray(imagem)
        L = 256
        linhas, colunas, canais = img.shape
        saida = np.zeros_like(img, dtype=np.uint8)

        half_m = m // 2
        half_n = n // 2

        for canal in range(canais):
            for i in range(linhas):
                for j in range(colunas):
                    i_ini = max(0, i - half_m)
                    i_fim = min(linhas, i + half_m + 1)
                    j_ini = max(0, j - half_n)
                    j_fim = min(colunas, j + half_n + 1)

                    janela = img[i_ini:i_fim, j_ini:j_fim, canal]

                    # histograma da janela
                    hist = np.bincount(janela.flatten(), minlength=L)

                    # CDF normalizada
                    cdf = np.cumsum(hist)
                    if cdf[-1] == 0:
                        cdf_norm = np.arange(L, dtype=np.uint8)
                    else:
                        cdf_norm = np.round((L - 1) * cdf / cdf[-1]).astype(np.uint8)

                    saida[i, j, canal] = cdf_norm[img[i, j, canal]]

        return saida

    def expansao_histograma(self, imagem=None, valor_min=None, valor_max=None, percentil_inferior=5, percentil_superior=95):
        """
        Expansão (contrast stretching) por canal usando percentis para aumentar contraste perceptível.
    
        Parâmetros:
            imagem: HxWxC (valores 0..255 ou escala int). Se None, usa self.imagem_original.
            valor_min, valor_max: limites manuais. Se None, usa percentis para definir faixa.
            percentil_inferior: percentil inferior usado para definir vmin automático.
            percentil_superior: percentil superior usado para definir vmax automático.
    
        Retorna:
            Imagem com contraste expandido, dtype uint8.
        """
        # aceita imagem opcional
        if imagem is None:
            img = np.asarray(self.imagem_original)
        else:
            img = np.asarray(imagem)
        
        saida = np.empty_like(img, dtype=np.uint8)
        linhas, colunas, canais = img.shape

        # calcular vmin/vmax usando percentis caso não tenham sido passados
        if valor_min is None:
            mins = np.percentile(img.reshape(-1, canais), percentil_inferior, axis=0)
        else:
            mins = np.array([valor_min] * canais) if np.isscalar(valor_min) else np.array(valor_min)

        if valor_max is None:
            maxs = np.percentile(img.reshape(-1, canais), percentil_superior, axis=0)
        else:
            maxs = np.array([valor_max] * canais) if np.isscalar(valor_max) else np.array(valor_max)

        # expansão canal a canal
        for c in range(canais):
            vmin = mins[c]
            vmax = maxs[c]
            canal = img[:, :, c].astype(np.float32)
            if vmax > vmin:
                stretched = (canal - vmin) / (vmax - vmin) * 255.0
            else:
                stretched = canal  # caso raro: imagem constante
            saida[:, :, c] = np.clip(np.round(stretched), 0, 255).astype(np.uint8)

        return saida

    def expansao_then_equalizacao(self, valor_min=None, valor_max=None):
        """
        Aplica expansão de histograma seguida de equalização global.
        Útil quando a imagem tem faixa estreita e queremos primeiro ampliar o contraste.
        """
        img_exp = self.expansao_histograma(valor_min=valor_min, valor_max=valor_max)
        img_eq = self.equalizacao_local(img_exp)
        return img_eq

    def equalizacao_then_expansao(self, valor_min=None, valor_max=None):
        """
        Aplica equalização global seguida de expansão. Esta ordem é menos comum,
        mas pode ser útil se a equalização reduzir a faixa e você quiser re-escalar.
        """
        img_eq = self.equalizacao_local()
        img_exp = self.expansao_histograma(img_eq, valor_min=valor_min, valor_max=valor_max)
        return img_exp
