import { zodResolver } from '@hookform/resolvers/zod';
import {
  IonButton,
  IonCard,
  IonCardContent,
  IonIcon,
  IonText,
  useIonRouter,
  useIonToast,
} from '@ionic/react';
import { add } from 'ionicons/icons';
import { useState } from 'react';
import { useFieldArray, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';

import { catalogApi } from '../../api/staff';
import type { Workout } from '../../api/types';
import { PATHS } from '../../auth/routing';
import { PageLayout } from '../../components/PageLayout';
import { ErrorState, ListSkeleton } from '../../components/States';
import { SelectField } from '../../components/form/fields';
import { TextField } from '../../components/form/TextField';
import { FormActions, FormSection, RowControls } from '../../components/staff/FormShell';
import { TranslationsSection } from '../../components/staff/TranslationsSection';
import { MediaPicker, type MediaChange } from '../../components/staff/MediaPicker';
import { useFormInit } from '../../hooks/useFormInit';
import { useLeaveForm } from '../../hooks/useLeaveForm';
import { useResource } from '../../hooks/useResource';
import { applyServerErrors, translateKey, uploadError } from '../../utils/errors';
import { toNumber } from '../../utils/numbers';
import { EMPTY_TRANSLATIONS, baseText, translationsForm } from '../../utils/translations';
import { workoutSchema, type WorkoutForm } from '../../validation/staff';

const EMPTY: WorkoutForm = {
  translations: EMPTY_TRANSLATIONS,
  name: '',
  description: '',
  durationMinutes: undefined,
  exercises: [],
};

const toForm = (workout: Workout): WorkoutForm => ({
  translations: translationsForm(workout.translations),
  name: baseText(workout, 'name', workout.name),
  description: baseText(workout, 'description', workout.description),
  durationMinutes: workout.durationMinutes ?? undefined,
  exercises: workout.exercises.map((item) => ({
    id: item.id,
    exerciseId: item.exercise.id,
    sets: item.sets,
    reps: item.reps,
    restSeconds: item.restSeconds,
  })),
});

/** Create / edit a workout (US-14, US-15). */
const WorkoutFormPage = () => {
  const { t } = useTranslation();
  const { id } = useParams<{ id?: string }>();
  const workoutId = id ? Number(id) : null;
  const router = useIonRouter();
  const leave = useLeaveForm(`${PATHS.catalog}?tab=workouts`);
  const [toast] = useIonToast();
  const [media, setMedia] = useState<MediaChange>({ remove: false });
  const [mediaError, setMediaError] = useState<string>();
  const [saveError, setSaveError] = useState<unknown>();
  // Created, but the file was refused: saving again updates it instead of creating another one.
  const [createdId, setCreatedId] = useState<number | null>(null);
  const exercises = useResource(() => catalogApi.exercises.list({ limit: 100 }));
  const existing = useResource(
    () => (workoutId ? catalogApi.workouts.get(workoutId) : Promise.resolve(null)),
    [workoutId],
  );

  const { control, handleSubmit, reset, setError, formState } = useForm<WorkoutForm>({
    resolver: zodResolver(workoutSchema),
    defaultValues: EMPTY,
  });
  const rows = useFieldArray({ control, name: 'exercises' });

  useFormInit(existing.data, reset, toForm);

  const options = [
    ...(exercises.data?.results ?? []),
    // Keep exercises that were deactivated but are still in this workout.
    ...(existing.data?.exercises.map((item) => item.exercise) ?? []),
  ]
    .filter((exercise, index, all) => all.findIndex((other) => other.id === exercise.id) === index)
    .map((exercise) => ({ value: exercise.id, label: exercise.name }));

  const back = () => router.goBack();

  const onSubmit = handleSubmit(async (values) => {
    setSaveError(undefined);
    setMediaError(undefined);
    try {
      const payload = {
        ...values,
        durationMinutes: values.durationMinutes ?? null,
        exercises: values.exercises.map((row) => ({ ...row, exerciseId: row.exerciseId! })),
      };
      const savedId = workoutId ?? createdId;
      const saved = savedId
        ? await catalogApi.workouts.update(savedId, payload)
        : await catalogApi.workouts.create(payload);
      setCreatedId(saved.id);
      if (media.file) await catalogApi.workouts.setMedia(saved.id, media.file, media.file.name);
      else if (media.remove) await catalogApi.workouts.removeMedia(saved.id);
      void toast({ message: t('common.saved'), duration: 2000, color: 'success' });
      leave(workoutId ? undefined : `${PATHS.catalog}/workouts/${saved.id}`);
    } catch (error) {
      const fileProblem = uploadError(t, error);
      if (fileProblem) setMediaError(fileProblem);
      else if (!applyServerErrors(error, setError)) setSaveError(error);
    }
  });

  const loading = exercises.loading || (workoutId !== null && existing.loading && !existing.data);
  const listError = translateKey(
    t,
    formState.errors.exercises?.root?.message ?? formState.errors.exercises?.message,
  );

  return (
    <PageLayout
      title={workoutId ? t('catalog.editWorkout') : t('catalog.new.workouts')}
      backHref={`${PATHS.catalog}?tab=workouts`}
      narrow
    >
      {loading && <ListSkeleton />}
      {existing.error && <ErrorState error={existing.error} onRetry={existing.reload} />}
      {!loading && !existing.error && (
        <form className="stack" onSubmit={onSubmit} noValidate>
          <TextField control={control} name="name" label={t('catalog.name')} required />
          <TextField
            control={control}
            name="description"
            label={t('catalog.description')}
            helperText={t('common.optional')}
          />
          <TextField
            control={control}
            name="durationMinutes"
            label={t('catalog.durationMinutes')}
            type="number"
            inputMode="numeric"
            parse={toNumber}
            helperText={t('catalog.durationHelp')}
          />
          <MediaPicker
            label={t('catalog.media')}
            currentUrl={existing.data?.mediaUrl ?? null}
            currentKind={existing.data?.mediaKind ?? null}
            value={media}
            onChange={(change) => {
              setMedia(change);
              setMediaError(undefined);
            }}
            serverError={mediaError}
          />

          <FormSection title={t('catalog.exercisesSection')}>
            {rows.fields.map((field, index) => (
              <IonCard key={field.id} data-testid={`workout-row-${index}`}>
                <IonCardContent className="stack">
                  <div className="row row--between">
                    <strong>{t('catalog.rowNumber', { number: index + 1 })}</strong>
                    <RowControls
                      index={index}
                      count={rows.fields.length}
                      onMove={rows.move}
                      onRemove={rows.remove}
                      label={t('catalog.rowNumber', { number: index + 1 })}
                    />
                  </div>
                  <SelectField
                    control={control}
                    name={`exercises.${index}.exerciseId`}
                    label={t('catalog.exercise')}
                    required
                    options={options}
                  />
                  <div
                    className="card-grid"
                    style={{ gridTemplateColumns: 'repeat(3, minmax(0, 1fr))' }}
                  >
                    <TextField
                      control={control}
                      name={`exercises.${index}.sets`}
                      label={t('training.sets')}
                      type="number"
                      inputMode="numeric"
                      parse={toNumber}
                      required
                    />
                    <TextField
                      control={control}
                      name={`exercises.${index}.reps`}
                      label={t('training.reps')}
                      type="number"
                      inputMode="numeric"
                      parse={toNumber}
                      required
                    />
                    <TextField
                      control={control}
                      name={`exercises.${index}.restSeconds`}
                      label={t('catalog.restSeconds')}
                      type="number"
                      inputMode="numeric"
                      parse={toNumber}
                      required
                    />
                  </div>
                </IonCardContent>
              </IonCard>
            ))}
            {listError && (
              <IonText color="danger" role="alert">
                <small>{listError}</small>
              </IonText>
            )}
            <IonButton
              fill="outline"
              onClick={() =>
                rows.append({ exerciseId: undefined, sets: 3, reps: 10, restSeconds: 60 })
              }
              data-testid="add-exercise-row"
            >
              <IonIcon slot="start" icon={add} aria-hidden="true" />
              {t('catalog.addExercise')}
            </IonButton>
          </FormSection>

          <TranslationsSection
            control={control}
            fields={[
              { key: 'name', label: t('catalog.name') },
              { key: 'description', label: t('catalog.description') },
            ]}
          />

          <FormActions onCancel={back} saving={formState.isSubmitting} error={saveError} />
        </form>
      )}
    </PageLayout>
  );
};

export default WorkoutFormPage;
