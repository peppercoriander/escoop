import { parse } from 'yaml';

export function parseUpdateLog(source) {
  const text = source.replace(/^\uFEFF/, '');
  const frontMatter = text.match(/^---[ \t]*\r?\n([\s\S]*?\r?\n)?---[ \t]*(?:\r?\n|$)/);
  const markdown = frontMatter ? text.slice(frontMatter[0].length) : text;
  let brief;

  if (frontMatter) {
    try {
      const metadata = parse(frontMatter[1] || '');
      if (typeof metadata?.brief === 'string') brief = metadata.brief.trim();
    } catch {
      // A malformed optional brief must not prevent the song catalog from loading.
    }
  }

  return {
    brief: brief || markdown.match(/^##[ \t]+(.+?)[ \t]*$/m)?.[1].trim(),
    markdown,
  };
}
