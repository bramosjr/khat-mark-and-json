// Opções de linha de comando do executável da interface: respondem no terminal
// e encerram, sem abrir a janela. Qualquer outro argumento é ignorado.

function helpText(version) {
  return [
    `Khat Mark And Json ${version}`,
    '',
    'Uso: khat-mark-and-json [--help | -h | --version]',
    '',
    'Sem opções, abre a interface gráfica.',
    '  -h, --help   mostra esta ajuda e sai',
    '  --version    mostra a versão e sai',
    '',
    'Para converter arquivos pelo terminal, use o markitdown-backend, que fica',
    'na pasta "resources" da instalação (veja o README).',
    '',
  ].join('\n');
}

// Devolve o texto a imprimir, ou null para seguir e abrir a interface.
function cliResponse(args, version) {
  const end = args.indexOf('--');
  const options = end === -1 ? args : args.slice(0, end);
  if (options.includes('--help') || options.includes('-h')) return helpText(version);
  if (options.includes('--version')) return `${version}\n`;
  return null;
}

module.exports = { cliResponse };
