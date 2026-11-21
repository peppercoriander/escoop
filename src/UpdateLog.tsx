import Markdown from 'react-markdown';
import updateMarkdown from '../update.md?raw';
import { parseUpdateLog } from './lib/update-log.mjs';
import styles from './App.module.css';

const updateLog = parseUpdateLog(updateMarkdown);
export const latestUpdate = updateLog.brief;

export default function UpdateLog() {
  return <section className={styles['update-log']} aria-label="更新记录">
    <nav aria-label="页面导航"><a className={styles['back-link']} href="#">返回歌曲一览</a></nav>
    <article className={styles['update-content']}>
      <Markdown>{updateLog.markdown}</Markdown>
    </article>
  </section>;
}
