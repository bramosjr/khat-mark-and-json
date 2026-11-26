// Texto que o app mostra, copia e salva a partir da resposta do backend.
// No JSON, o texto precisa ser JSON puro: é o conteúdo do arquivo .json.
export function formatResult(targetFormat, data) {
  return targetFormat === 'json'
    ? JSON.stringify(data.json_data, null, 2)
    : data.markdown;
}
