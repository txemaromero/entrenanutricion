import { zodResolver } from '@hookform/resolvers/zod';
import {
  IonButton,
  IonCard,
  IonCardContent,
  IonIcon,
  IonText,
  IonThumbnail,
  useIonRouter,
  useIonToast,
} from '@ionic/react';
import { add, cloudUploadOutline, trashOutline } from 'ionicons/icons';
import { useRef, useState } from 'react';
import { useFieldArray, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';

import { catalogApi } from '../../api/staff';
import type { Exercise } from '../../api/types';
import { PATHS } from '../../auth/routing';
import { PageLayout } from '../../components/PageLayout';
import { ErrorState, ListSkeleton } from '../../components/States';
import { ChipMultiSelect } from '../../components/form/fields';
import { TextField } from '../../components/form/TextField';
import { FormActions, FormSection, RowControls } from '../../components/staff/FormShell';
import { TranslationsSection } from '../../components/staff/TranslationsSection';
import { useConfirm } from '../../hooks/useConfirm';
import { useFormInit } from '../../hooks/useFormInit';
import { useLeaveForm } from '../../hooks/useLeaveForm';
import { useResource } from '../../hooks/useResource';
import { applyServerErrors, errorMessage, uploadError } from '../../utils/errors';
import { checkMediaFile, MEDIA_ACCEPT } from '../../utils/media';
import { EMPTY_TRANSLATIONS, baseText, translationsForm } from '../../utils/translations';
import { exerciseSchema, type ExerciseForm } from '../../validation/staff';

const EMPTY: ExerciseForm = {
  translations: EMPTY_TRANSLATIONS,
  name: '',
  description: '',
  technique: '',
  commonMistakes: '',
  benefits: '',
  muscleGroupIds: [],
  steps: [],
};

// The Spanish texts are edited from `translations.es` (the other fields come in the screen's language).
const toForm = (exercise: Exercise): ExerciseForm => ({
  translations: translationsForm(exercise.translations, { steps: true }),
  name: baseText(exercise, 'name', exercise.name),
  description: baseText(exercise, 'description', exercise.description),
  technique: baseText(exercise, 'technique', exercise.technique),
  commonMistakes: baseText(exercise, 'commonMistakes', exercise.commonMistakes),
  benefits: baseText(exercise, 'benefits', exercise.benefits),
  muscleGroupIds: exercise.muscleGroups.map((group) => String(group.id)),
  steps: (exercise.translations?.es?.steps ?? exercise.steps).map((text) => ({ text })),
});

/** Create / edit an exercise (US-17) with steps, muscle groups and several media files. */
const ExerciseFormPage = () => {
  const { t } = useTranslation();
  const { id } = useParams<{ id?: string }>();
  const exerciseId = id ? Number(id) : null;
  const router = useIonRouter();
  const leave = useLeaveForm(`${PATHS.catalog}?tab=exercises`);
  const confirm = useConfirm();
  const [toast] = useIonToast();
  const fileInput = useRef<HTMLInputElement>(null);
  const [newFiles, setNewFiles] = useState<File[]>([]);
  const [fileError, setFileError] = useState<string>();
  const [saveError, setSaveError] = useState<unknown>();
  // Created, but a file was refused: saving again updates it instead of creating another one.
  const [createdId, setCreatedId] = useState<number | null>(null);
  const groups = useResource(catalogApi.muscleGroups);
  const existing = useResource(
    () => (exerciseId ? catalogApi.exercises.get(exerciseId) : Promise.resolve(null)),
    [exerciseId],
  );

  const { control, handleSubmit, reset, setError, formState } = useForm<ExerciseForm>({
    resolver: zodResolver(exerciseSchema),
    defaultValues: EMPTY,
  });
  const steps = useFieldArray({ control, name: 'steps' });

  useFormInit(existing.data, reset, toForm);

  const addFiles = (files: FileList | null) => {
    const accepted: File[] = [];
    Array.from(files ?? []).forEach((file) => {
      const problem = checkMediaFile(file);
      if (problem) setFileError(t(problem));
      else accepted.push(file);
    });
    if (accepted.length) setFileError(undefined);
    setNewFiles((current) => [...current, ...accepted]);
  };

  const deleteExistingMedia = async (mediaId: number) => {
    if (!exerciseId) return;
    const ok = await confirm({
      header: t('staff.deleteTitle'),
      message: t('catalog.deleteMedia'),
      confirmText: t('common.delete'),
      destructive: true,
    });
    if (!ok) return;
    try {
      await catalogApi.exercises.removeMedia(exerciseId, mediaId);
      await existing.reload();
    } catch (error) {
      void toast({ message: errorMessage(t, error), duration: 3000, color: 'danger' });
    }
  };

  const onSubmit = handleSubmit(async (values) => {
    setSaveError(undefined);
    setFileError(undefined);
    try {
      const payload = {
        ...values,
        muscleGroupIds: values.muscleGroupIds.map(Number),
        steps: values.steps.map((step) => step.text.trim()),
      };
      const savedId = exerciseId ?? createdId;
      const saved = savedId
        ? await catalogApi.exercises.update(savedId, payload)
        : await catalogApi.exercises.create(payload);
      setCreatedId(saved.id);
      for (const file of newFiles) {
        await catalogApi.exercises.addMedia(saved.id, file, file.name);
        // Uploaded: if a later file is refused, saving again does not send this one twice.
        setNewFiles((current) => current.filter((pending) => pending !== file));
      }
      void toast({ message: t('common.saved'), duration: 2000, color: 'success' });
      leave(exerciseId ? undefined : `${PATHS.catalog}/exercises/${saved.id}`);
    } catch (error) {
      const fileProblem = uploadError(t, error);
      if (fileProblem) setFileError(fileProblem);
      else if (!applyServerErrors(error, setError)) setSaveError(error);
    }
  });

  const loading = groups.loading || (exerciseId !== null && existing.loading && !existing.data);

  return (
    <PageLayout
      title={exerciseId ? t('catalog.editExercise') : t('catalog.new.exercises')}
      backHref={`${PATHS.catalog}?tab=exercises`}
      narrow
    >
      {loading && <ListSkeleton />}
      {existing.error && <ErrorState error={existing.error} onRetry={existing.reload} />}
      {!loading && !existing.error && (
        <form className="stack" onSubmit={onSubmit} noValidate>
          <TextField control={control} name="name" label={t('catalog.name')} required />
          <TextField control={control} name="description" label={t('catalog.description')} />
          <ChipMultiSelect
            control={control}
            name="muscleGroupIds"
            label={t('exercise.muscleGroups')}
            options={(groups.data ?? []).map((group) => ({
              value: String(group.id),
              label: t(`enums.muscleGroup.${group.slug}`, { defaultValue: group.name }),
            }))}
          />

          <FormSection title={t('exercise.steps')}>
            {steps.fields.map((field, index) => (
              <div key={field.id} className="row" style={{ alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                  <TextField
                    control={control}
                    name={`steps.${index}.text`}
                    label={t('catalog.stepNumber', { number: index + 1 })}
                    required
                  />
                </div>
                <RowControls
                  index={index}
                  count={steps.fields.length}
                  onMove={steps.move}
                  onRemove={steps.remove}
                  label={t('catalog.stepNumber', { number: index + 1 })}
                />
              </div>
            ))}
            <IonButton
              fill="outline"
              onClick={() => steps.append({ text: '' })}
              data-testid="add-step"
            >
              <IonIcon slot="start" icon={add} aria-hidden="true" />
              {t('catalog.addStep')}
            </IonButton>
          </FormSection>

          <TextField control={control} name="technique" label={t('exercise.technique')} />
          <TextField control={control} name="commonMistakes" label={t('exercise.commonMistakes')} />
          <TextField control={control} name="benefits" label={t('exercise.benefits')} />

          <FormSection title={t('catalog.media')}>
            {existing.data?.media.map((item) => (
              <IonCard key={item.id}>
                <IonCardContent className="row row--between">
                  <span className="row">
                    {item.kind === 'image' && (
                      <IonThumbnail>
                        <img src={item.url} alt="" />
                      </IonThumbnail>
                    )}
                    {t(`enums.mediaKind.${item.kind}`)}
                  </span>
                  <IonButton
                    fill="clear"
                    color="danger"
                    onClick={() => void deleteExistingMedia(item.id)}
                    aria-label={t('staff.removeMedia')}
                  >
                    <IonIcon slot="icon-only" icon={trashOutline} aria-hidden="true" />
                  </IonButton>
                </IonCardContent>
              </IonCard>
            ))}
            {newFiles.map((file, index) => (
              <div key={`${file.name}-${index}`} className="row row--between">
                <span>{file.name}</span>
                <IonButton
                  fill="clear"
                  color="danger"
                  onClick={() => setNewFiles((current) => current.filter((_, i) => i !== index))}
                  aria-label={t('staff.removeMedia')}
                >
                  <IonIcon slot="icon-only" icon={trashOutline} aria-hidden="true" />
                </IonButton>
              </div>
            ))}
            <input
              ref={fileInput}
              type="file"
              accept={MEDIA_ACCEPT}
              multiple
              hidden
              onChange={(event) => addFiles(event.target.files)}
              data-testid="media-input"
            />
            <IonButton fill="outline" onClick={() => fileInput.current?.click()}>
              <IonIcon slot="start" icon={cloudUploadOutline} aria-hidden="true" />
              {t('staff.uploadMedia')}
            </IonButton>
            {fileError && (
              <IonText color="danger" role="alert">
                <small>{fileError}</small>
              </IonText>
            )}
          </FormSection>

          <TranslationsSection
            control={control}
            stepsField="steps"
            fields={[
              { key: 'name', label: t('catalog.name') },
              { key: 'description', label: t('catalog.description') },
              { key: 'technique', label: t('exercise.technique') },
              { key: 'commonMistakes', label: t('exercise.commonMistakes') },
              { key: 'benefits', label: t('exercise.benefits') },
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

export default ExerciseFormPage;
