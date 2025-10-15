# Sistema para exibir, manipular e salvar imagens
Sistema de manipulação de imagens desenvolvido na cadeira de PDI


<section>
  <h1>📘 Relatório Teórico – Processamento Digital de Imagens</h1>

  <h2>1. Representação de Imagens RGB (24 bits/pixel)</h2>
  <p>
    Uma imagem digital RGB é formada por três camadas de cor: <strong>vermelho (R)</strong>, <strong>verde (G)</strong> e <strong>azul (B)</strong>.
    Cada pixel contém três valores inteiros (um por canal) no intervalo <code>[0, 255]</code>.
  </p>
  <ul>
    <li>Cada canal tem <strong>8 bits</strong> (256 níveis); juntos totalizam <strong>24 bits/pixel</strong>.</li>
    <li>Exemplo de pixel: <code>(R=120, G=200, B=50)</code>.</li>
    <li>Até <strong>16,7 milhões</strong> de cores (256³).</li>
  </ul>

  <hr>

  <h2>2. Correlação Bidimensional <em>m × n</em></h2>

  <h3>2.1. Conceito</h3>
  <p>
    A <strong>correlação 2D</strong> aplica uma máscara (kernel) sobre a imagem, combinando valores de vizinhança para cada pixel.
  </p>
  <p><strong>Fórmula (por canal):</strong></p>
  <pre><code>y(i, j) =  Σ(u=0..m-1) Σ(v=0..n-1) [ x(i+u, j+v) · h(u, v) ] + bias</code></pre>
  <ul>
    <li><code>x(i, j)</code>: valor original do pixel.</li>
    <li><code>h(u, v)</code>: valor da máscara na posição <code>(u, v)</code>.</li>
    <li><code>m × n</code>: dimensões do kernel.</li>
    <li><code>bias</code>: deslocamento inteiro entre <code>-255</code> e <code>255</code> (ajusta brilho).</li>
  </ul>

  <h3>2.2. Funções de Ativação</h3>
  <ul>
    <li><strong>Identidade</strong>: <code>f(x) = x</code> (mantém o valor calculado).</li>
    <li><strong>ReLU</strong>: <code>f(x) = max(0, x)</code> (trunca valores negativos, útil para realçar bordas).</li>
  </ul>

  <h3>2.3. Filtros Utilizados</h3>
  <h4>Filtro Gaussiano 5×5</h4>
  <ul>
    <li>Suaviza a imagem (reduz ruído) com borramento <em>suave</em>.</li>
    <li>Kernel aproxima uma distribuição Gaussiana bidimensional.</li>
  </ul>

  <h4>Filtros Box (1×10, 10×1, 10×10)</h4>
  <ul>
    <li>Máscaras com valores iguais; realizam <strong>média</strong> na vizinhança.</li>
    <li><code>Box 1×10</code>: suavização horizontal; <code>Box 10×1</code>: vertical; <code>Box 10×10</code>: média em bloco grande (borramento forte).</li>
  </ul>

  <h4>Sobel Horizontal e Vertical</h4>
  <ul>
    <li>Detectam <strong>bordas</strong> (gradientes de intensidade).</li>
    <li>Sobel Horizontal realça mudanças verticais (bordas horizontais).</li>
    <li>Sobel Vertical realça mudanças horizontais (bordas verticais).</li>
  </ul>

  <div style="display:flex; gap:24px; flex-wrap:wrap; align-items:flex-start;">
    <div>
      <p><strong>Sobel Vertical (S<sub>x</sub>):</strong></p>
      <table border="1" cellpadding="6" cellspacing="0">
        <tbody>
          <tr><td>-1</td><td>0</td><td>1</td></tr>
          <tr><td>-2</td><td>0</td><td>2</td></tr>
          <tr><td>-1</td><td>0</td><td>1</td></tr>
        </tbody>
      </table>
    </div>
    <div>
      <p><strong>Sobel Horizontal (S<sub>y</sub>):</strong></p>
      <table border="1" cellpadding="6" cellspacing="0">
        <tbody>
          <tr><td>-1</td><td>-2</td><td>-1</td></tr>
          <tr><td>0</td><td>0</td><td>0</td></tr>
          <tr><td>1</td><td>2</td><td>1</td></tr>
        </tbody>
      </table>
    </div>
  </div>

  <h3>2.4. Visualização de Sobel</h3>
  <ol>
    <li>Aplicar <strong>valor absoluto</strong> à resposta (remove negativos).</li>
    <li>Aplicar <strong>expansão de histograma</strong> para <code>[0, 255]</code> (maximiza contraste das bordas).</li>
  </ol>

  <hr>

  <h2>3. Equalização de Histograma</h2>

  <h3>3.1. Conceito</h3>
  <p>
    Redistribui níveis de intensidade para melhorar o <strong>contraste</strong>. Baseia-se no histograma e na sua <strong>CDF</strong>
    (função de distribuição acumulada).
  </p>
  <p><strong>Passos:</strong></p>
  <ol>
    <li>Calcular o <strong>histograma</strong> (contagem por intensidade).</li>
    <li>Calcular a <strong>CDF</strong> (soma acumulada do histograma).</li>
    <li>Aplicar transformação:</li>
  </ol>
  <pre><code>T(r) = round( ((L - 1) / RC) * Σ(k=0..r) n_k )</code></pre>
  <ul>
    <li><code>L = 256</code> (níveis de intensidade).</li>
    <li><code>RC</code> = total de pixels (linhas × colunas).</li>
    <li><code>n_k</code> = contagem de pixels com intensidade <code>k</code>.</li>
  </ul>
  <p>Resultado: os níveis passam a ocupar melhor a faixa <code>[0, 255]</code>.</p>

  <hr>

  <h2>4. Equalização Local + Expansão de Histograma</h2>

  <h3>4.1. Por que Local?</h3>
  <p>
    Em imagens com iluminação desigual, a equalização <strong>global</strong> pode falhar. Dividir a imagem em blocos
    <strong><em>m × n</em></strong> e equalizar cada um separadamente adapta o contraste às diferentes regiões.
  </p>

  <h3>4.2. Expansão de Histograma (por bloco)</h3>
  <ol>
    <li>Obter <code>r_min</code> e <code>r_max</code> do bloco equalizado.</li>
    <li>Aplicar a expansão linear para todo o bloco:</li>
  </ol>
  <pre><code>s = ((r - r_min) / (r_max - r_min)) * 255</code></pre>
  <p>
    Isso distribui os níveis do bloco por toda a faixa <code>[0, 255]</code>, garantindo <strong>contraste máximo local</strong>.
  </p>

  <h3>4.3. Resultado</h3>
  <ul>
    <li>Regiões escuras tornam-se mais claras.</li>
    <li>Regiões claras ganham contraste.</li>
    <li>Detalhes e bordas em áreas pouco iluminadas ficam mais visíveis.</li>
  </ul>

  <hr>

  <h2>5. Observações de Implementação (Resumo dos Requisitos)</h2>
  <ul>
    <li>Abrir, exibir, manipular e salvar imagens RGB (24 bits/pixel, 8 bits por canal).</li>
    <li>Correlação 2D <em>m × n</em> com <strong>bias</strong> (−255 a 255) e ativação (<strong>Identidade</strong> ou <strong>ReLU</strong>).</li>
    <li>Leitura de <strong>filtros</strong> a partir de arquivo <code>.txt</code> (máscara, bias, ativação).</li>
    <li>Testes com: <strong>Gaussiano 5×5</strong>, <strong>Box 1×10</strong>, <strong>Box 10×1</strong>, <strong>Box 10×10</strong>, <strong>Sobel Horizontal</strong>, <strong>Sobel Vertical</strong>.</li>
    <li>Para Sobel: aplicar <strong>|valor|</strong> + <strong>expansão de histograma para [0,255]</strong>.</li>
    <li>Equalização seguida de <strong>expansão de histograma local</strong> (janela <em>m × n</em>) em cada canal R, G e B.</li>
  </ul>
</section>