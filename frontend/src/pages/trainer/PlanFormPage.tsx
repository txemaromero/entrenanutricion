import { zodResolver } from '@hookform/resolvers/zod';
import {
  IonButton,
  IonCard,
  IonCardContent,
  IonIcon,
  IonSelect,
  IonSelectOption,
  IonText,
  useIonRouter,
  useIonToast,
} from '@ionic/react';
import { add } from 'ionicons/icons';
import { useState } from 'react';
import { useFieldArray, useForm, useWatch, type DefaultValues } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useLocation, useParams } from 'react-router-dom';

import { catalogApi } from '../../api/staff';
import type { TrainingPlan } from '../../api/types';
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
import { returnToParam } from '../../utils/lists';
import { toNumber } from '../../utils/numbers';
import { EQUIPMENT, GOALS } from '../../validation/onboarding';
import { DIFFICULTIES, planSchema, type PlanForm } from '../../validation/staff';
import { EMPTY_TRANSLATIONS, baseText, translationsForm } from '../../utils/translations';

const EMPTY: DefaultValues<PlanForm> = {
  translations: EMPTY_TRANSLATIONS,
  name: '',
  description: '',
  durationWeeks: 8,
  workouts: [],
};

const toForm = (plan: TrainingPlan): PlanForm => ({
  translations: translationsForm(plan.translations),
  name: baseText(plan, 'name', plan.name),
  description: baseText(plan, 'description', plan.description),
  goal: plan.goal,
  difficulty: plan.difficulty,
  equipment: plan.equipment,
  durationWeeks: plan.durationWeeks,
  workouts: plan.workouts.map((row) => ({ id: row.id, workoutId: row.workout.id })),
});

/**
 * Create / edit a training plan (US-18). With `?returnTo=` (from Assignments, "create new plan")
 * it goes back there with the new plan preselected.
 */
const PlanFormPage = () => {
  const { t } = useTranslation();
  const { id } = useParams<{ id?: string }>();
  const planId = id ? Number(id) : null;
  const location = useLocation();
  const returnTo = returnToParam(location.search);
  const router = useIonRouter();
  const leave = useLeaveForm(`${PATHS.catalog}?tab=plans`);
  const [toast] = useIonToast();
  const [media, setMedia] = useState<MediaChange>({ remove: false });
  const [mediaError, setMediaError] = useState<string>();
  const [saveError, setSaveError] = useState<unknown>();
  // Created, but the file was refused: saving again updates it instead of creating another one.
  const [createdId, setCreatedId] = useState<number | null>(null);
  const [toAdd, setToAdd] = useState<number>();
  const workouts = useResource(() => catalogApi.workouts.list({ limit: 100 }));
  const existing = useResource(
    () => (planId ? catalogApi.plans.get(planId) : Promise.resolve(null)),
    [planId],
  );

  const { control, handleSubmit, reset, setError, formState } = useForm<PlanForm>({
    resolver: zodResolver(planSchema),
    defaultValues: EMPTY,
  });
  const rows = useFieldArray({ control, name: 'workouts' });
  const selected = useWatch({ control, name: 'workouts' });

  useFormInit(existing.data, reset, toForm);

  const workoutName = (workoutId: number) =>
    workouts.data?.results.find((workout) => workout.id === workoutId)?.name ??
    existing.data?.workouts.find((row) => row.workout.id === workoutId)?.workout.name ??
    `#${workoutId}`;

  const onSubmit = handleSubmit(async (values) => {
    setSaveError(undefined);
    setMediaError(undefined);
    try {
      const savedId = planId ?? createdId;
      const saved = savedId
        ? await catalogApi.plans.update(savedId, values)
        : await catalogApi.plans.create(values);
      setCreatedId(saved.id);
      if (media.file) await catalogApi.plans.setMedia(saved.id, media.file, media.file.name);
      else if (media.remove) await catalogApi.plans.removeMedia(saved.id);
      void toast({ message: t('common.saved'), duration: 2000, color: 'success' });
      if (returnTo) router.push(`${returnTo}?trainingPlan=${saved.id}`, 'back', 'replace');
      else leave(planId ? undefined : `${PATHS.catalog}/plans/${saved.id}`);
    } catch (error) {
      const fileProblem = uploadError(t, error);
      if (fileProblem) setMediaError(fileProblem);
      else if (!applyServerErrors(error, setError)) setSaveError(error);
    }
  });

  const loading = workouts.loading || (planId !== null && existing.loading && !existing.data);
  const listError = translateKey(
    t,
    formState.errors.workouts?.root?.message ?? formState.errors.workouts?.message,
  );
  const options = (list: readonly string[], group: string) =>
    list.map((value) => ({ value, label: t(`enums.${group}.${value}`) }));

  return (
    <PageLayout
      title={planId ? t('catalog.editPlan') : t('catalog.new.plans')}
      backHref={returnTo ?? `${PATHS.catalog}?tab=plans`}
      narrow
    >
      {loading && <ListSkeleton />}
      {existing.error && <ErrorState error={existing.error} onRetry={existing.reload} />}
      {!loading && !existing.error && (
        <form className="stack" onSubmit={onSubmit} noValidate>
          <TextField control={control} name="name" label={t('catalog.name')} required />
          <TextField control={control} name="description" label={t('catalog.description')} />
          <SelectField
            control={control}
            name="goal"
            label={t('profile.goal')}
            required
            options={options(GOALS, 'goal')}
          />
          <SelectField
            control={control}
            name="difficulty"
            label={t('catalog.difficulty')}
            required
            options={options(DIFFICULTIES, 'difficulty')}
          />
          <SelectField
            control={control}
            name="equipment"
            label={t('catalog.equipment')}
            required
            options={options(EQUIPMENT, 'equipment')}
          />
          <TextField
            control={control}
            name="durationWeeks"
            label={t('catalog.durationWeeks')}
            type="number"
            inputMode="numeric"
            parse={toNumber}
            required
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

          <FormSection title={t('catalog.workoutSequence')}>
            {rows.fields.map((field, index) => (
              <IonCard key={field.id} data-testid={`plan-row-${index}`}>
                <IonCardContent className="row row--between">
                  <span>
                    <strong>{index + 1}.</strong>{' '}
                    {workoutName(selected?.[index]?.workoutId ?? field.workoutId)}
                  </span>
                  <RowControls
                    index={index}
                    count={rows.fields.length}
                    onMove={rows.move}
                    onRemove={rows.remove}
                    label={workoutName(field.workoutId)}
                  />
                </IonCardContent>
              </IonCard>
            ))}
            {listError && (
              <IonText color="danger" role="alert">
                <small>{listError}</small>
              </IonText>
            )}
            <div className="row">
              <IonSelect
                label={t('catalog.workout')}
                labelPlacement="floating"
                fill="outline"
                interface="popover"
                value={toAdd}
                onIonChange={(event) => setToAdd(event.detail.value)}
                style={{ flex: 1 }}
                data-testid="plan-workout-select"
              >
                {workouts.data?.results.map((workout) => (
                  <IonSelectOption key={workout.id} value={workout.id}>
                    {workout.name}
                  </IonSelectOption>
                ))}
              </IonSelect>
              <IonButton
                disabled={!toAdd}
                onClick={() => {
                  if (toAdd) rows.append({ workoutId: toAdd });
                  setToAdd(undefined);
                }}
                data-testid="add-plan-workout"
              >
                <IonIcon slot="start" icon={add} aria-hidden="true" />
                {t('common.add')}
              </IonButton>
            </div>
          </FormSection>

          <TranslationsSection
            control={control}
            fields={[
              { key: 'name', label: t('catalog.name') },
              { key: 'description', label: t('catalog.description') },
            ]}
          />

          <FormActions
            onCancel={() => router.goBack()}
            saving={formState.isSubmitting}
            error={saveError}
          />
        </form>
      )}
    </PageLayout>
  );
};

export default PlanFormPage;
