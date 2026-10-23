import { useState } from 'react';
import { View } from 'react-native';

import { useI18n } from '../i18n';
import { useTheme } from '../theme';
import { fieldErrors } from '../utils/format';
import { Button, Chip, ErrorView, Field, Row, Switch, T, TextLink } from './ui';

const ALL_DAYS = [0, 1, 2, 3, 4, 5, 6]; // Sunday = 0, as the API expects
const sameDays = (a, b) => (a || ALL_DAYS).join() === (b || ALL_DAYS).join();

/**
 * Edit a remedy (`initial` = serialized remedy) or write a custom one (`initial` undefined): text,
 * daily count, days and reminder. `onSubmit(patch)` gets only what changed for an existing remedy;
 * `onReset` clears all edits; `onRemove` removes the remedy.
 */
export function RemedyForm({ initial, onSubmit, onReset, onRemove }) {
  const th = useTheme();
  const { t } = useI18n();
  const custom = !initial || initial.kind === 'custom';
  const [title, setTitle] = useState(initial?.title || '');
  const [text, setText] = useState(initial?.text || '');
  const [how, setHow] = useState(initial?.how || '');
  const [target, setTarget] = useState(String(initial?.target ?? 1));
  const [days, setDays] = useState(initial?.weekdays || null); // null = every day
  const [reminder, setReminder] = useState(initial?.reminder ?? true);
  const [tried, setTried] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const server = fieldErrors(error);
  const weekdayNames = t('remedies.weekdays');

  const n = Number(target);
  const targetOk = Number.isInteger(n) && n >= 1 && n <= 100000;
  const errs = tried ? {
    title: custom && !title.trim() ? t('remedies.titleRequired') : server.title,
    target: !targetOk ? t('remedies.targetInvalid') : server.target,
  } : {};

  const toggleDay = (d) => {
    const cur = days || ALL_DAYS;
    const next = cur.includes(d) ? cur.filter((x) => x !== d) : [...cur, d].sort();
    if (!next.length) return; // at least one day
    setDays(next.length === 7 ? null : next);
  };

  const submit = async () => {
    setTried(true);
    if ((custom && !title.trim()) || !targetOk) return;
    const body = {};
    const put = (k, v, was) => { if (custom || v !== was) body[k] = v; };
    put('title', title.trim(), initial?.title);
    put('text', text.trim(), initial?.text || '');
    put('how', how.trim(), initial?.how || '');
    put('target', n, initial?.target);
    if (custom || !sameDays(days, initial?.weekdays)) body.weekdays = days || ALL_DAYS;
    put('reminder', reminder, initial?.reminder);
    setBusy(true);
    setError(null);
    try {
      await onSubmit(body);
    } catch (e) {
      setError(e);
      setBusy(false);
    }
  };

  const run = (action) => async () => {
    setBusy(true);
    setError(null);
    try {
      await action();
    } catch (e) {
      setError(e);
    }
    setBusy(false);
  };

  return (
    <View>
      {!Object.keys(server).length ? <ErrorView error={error} /> : null}
      <View style={{ gap: 14 }}>
        <Field label={t('remedies.fTitle')} value={title} onChangeText={setTitle} placeholder={t('remedies.fTitlePh')}
          maxLength={120} error={errs.title} />
        <Field label={t('remedies.fText')} value={text} onChangeText={setText} placeholder={t('remedies.fTextPh')}
          maxLength={300} multiline error={server.text} />
        <Field label={t('remedies.fHow')} value={how} onChangeText={setHow} placeholder={t('remedies.fHowPh')}
          maxLength={2000} multiline inputStyle={{ minHeight: 84, textAlignVertical: 'top' }} error={server.how} />
        <View>
          <Field label={t('remedies.fTarget')} value={target} onChangeText={(v) => setTarget(v.replace(/[^0-9]/g, ''))}
            keyboardType="number-pad" maxLength={6} error={errs.target} />
          {!errs.target ? <T v="caption" style={{ marginTop: 6 }}>{t('remedies.fTargetHint')}</T> : null}
        </View>
        <View>
          <T v="label" style={{ marginBottom: 8 }}>{t('remedies.fDays')}</T>
          <Row gap={7} style={{ flexWrap: 'wrap' }}>
            <Chip label={t('remedies.everyDay')} active={!days} onPress={() => setDays(null)} />
            {ALL_DAYS.map((d) => (
              <Chip key={d} label={weekdayNames[d]} active={!!days && days.includes(d)} onPress={() => toggleDay(d)} />
            ))}
          </Row>
          {server.weekdays ? <T v="caption" style={{ color: th.kind.bad.solid, marginTop: 6 }}>{server.weekdays}</T> : null}
        </View>
        <Row gap={12} style={{ paddingVertical: 4 }}>
          <View style={{ flex: 1 }}>
            <T v="label">{t('remedies.reminder')}</T>
            <T v="caption" style={{ marginTop: 2 }}>{t('remedies.reminderSub')}</T>
          </View>
          <Switch value={reminder} onChange={() => setReminder((v) => !v)} />
        </Row>
      </View>
      <Button title={t('remedies.save')} onPress={submit} loading={busy} style={{ marginTop: 24 }} />
      {!custom && initial?.edited && onReset ? (
        <View style={{ alignItems: 'center', marginTop: 16 }}>
          <TextLink title={t('remedies.reset')} onPress={busy ? undefined : run(onReset)} />
        </View>
      ) : null}
      {initial && onRemove ? (
        <View style={{ alignItems: 'center', marginTop: 16 }}>
          <TextLink title={t('remedies.remove')} onPress={busy ? undefined : run(onRemove)} style={{ color: th.kind.bad.solid }} />
        </View>
      ) : null}
    </View>
  );
}
