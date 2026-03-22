"use client";
import { useParams, useRouter } from "next/navigation";
import { useState, useCallback, useEffect } from "react";
import { FormProvider, useForm, FormData } from "@/components/detail-form/FormContext";
import StepIndicator from "@/components/detail-form/StepIndicator";
import Step1Destinations from "@/components/detail-form/Step1Destinations";
import Step2Party from "@/components/detail-form/Step2Party";
import Step3Budget from "@/components/detail-form/Step3Budget";
import Step4Interests from "@/components/detail-form/Step4Interests";
import Step5Pace from "@/components/detail-form/Step5Pace";
import Step6Transport from "@/components/detail-form/Step6Transport";
import { ArrowLeftIcon, ArrowRightIcon, CheckIcon } from "@heroicons/react/24/outline";

// ── 每步校验规则 ───────────────────────────────────────────────────────────
function validateStep(step: number, data: FormData): Record<string, string> {
  const errs: Record<string, string> = {};
  if (step === 1) {
    if (data.cities.length === 0) errs.cities = "请至少选择一个目的地城市";
    if (!data.travel_start_date) errs.travel_start_date = "请选择出发日期";
  }
  if (step === 2) {
    if (!data.party_type) errs.party_type = "请选择出行类型";
    if (data.party_size < 1) errs.party_size = "出行人数至少为 1 人";
  }
  return errs;
}

// ── 步骤组件映射 ──────────────────────────────────────────────────────────
const STEP_COMPONENTS = [Step1Destinations, Step2Party, Step3Budget, Step4Interests, Step5Pace, Step6Transport];

// ── 内层表单控制器 ─────────────────────────────────────────────────────────
function DetailFormInner({ formId }: { formId: string }) {
  const router = useRouter();
  const { data, currentStep, setStep, saving, setSaving, errors, setErrors } = useForm();
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [submitSuccess, setSubmitSuccess] = useState(false);

  const StepComponent = STEP_COMPONENTS[currentStep - 1];

  // 自动保存当前步骤到后端
  const saveCurrentStep = useCallback(
    async (stepData: Partial<FormData>) => {
      try {
        await fetch(`/api/detail-forms/${formId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ...stepData, current_step: currentStep }),
        });
      } catch {
        // 静默失败，不阻塞用户
      }
    },
    [formId, currentStep]
  );

  const goNext = async () => {
    const errs = validateStep(currentStep, data);
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }
    setErrors({});
    setSaving(true);
    await saveCurrentStep(data);
    setSaving(false);
    setCompletedSteps((prev) => new Set([...prev, currentStep]));
    setStep(Math.min(6, currentStep + 1));
  };

  const goPrev = () => {
    setErrors({});
    setStep(Math.max(1, currentStep - 1));
  };

  const handleSubmit = async () => {
    const errs = validateStep(currentStep, data);
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }
    setSaving(true);
    try {
      // 保存最后一步
      await fetch(`/api/detail-forms/${formId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...data, current_step: 6 }),
      });
      // 提交表单
      const res = await fetch(`/api/detail-forms/${formId}/submit`, {
        method: "POST",
      });
      if (res.ok) {
        setCompletedSteps(new Set([1, 2, 3, 4, 5, 6]));
        setSubmitSuccess(true);
        // 不跳转，留在当前页继续编辑
      }
    } catch (e) {
      console.error("Submit failed", e);
    } finally {
      setSaving(false);
    }
  };

  // 提交成功状态 — 不跳转，可以继续编辑
  if (submitSuccess) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-emerald-50 flex items-center justify-center px-4">
        <div className="text-center space-y-4 max-w-sm">
          <div className="w-20 h-20 rounded-full bg-emerald-500 flex items-center justify-center mx-auto shadow-lg">
            <CheckIcon className="w-10 h-10 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900">保存成功！</h2>
          <p className="text-gray-600 text-sm leading-relaxed">
            您的需求已保存，客服会与您微信确认细节。<br />
            如果有修改可以随时打开此链接再次编辑。
          </p>
          <button
            onClick={() => setSubmitSuccess(false)}
            className="mt-2 text-sm text-indigo-600 hover:text-indigo-800 font-medium"
          >
            ← 继续编辑
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* 顶栏 */}
      <header className="bg-white border-b border-gray-100 px-4 py-3 flex items-center gap-3">
        <button onClick={() => router.back()} className="text-gray-400 hover:text-gray-600">
          <ArrowLeftIcon className="w-5 h-5" />
        </button>
        <div className="flex-1">
          <h1 className="text-base font-semibold text-gray-900">完善行程信息</h1>
          <p className="text-xs text-gray-500">填写越详细，行程越贴合您的需求</p>
        </div>
      </header>

      {/* 步骤指示器 */}
      <StepIndicator
        currentStep={currentStep}
        onStepClick={setStep}
        completedSteps={completedSteps}
      />

      {/* 表单内容区 */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-md mx-auto px-4 py-6 pb-32">
          <StepComponent />
        </div>
      </div>

      {/* 底部操作栏（固定） */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 px-4 py-3 safe-pb">
        <div className="max-w-md mx-auto flex gap-3">
          {currentStep > 1 && (
            <button
              onClick={goPrev}
              disabled={saving}
              className="flex items-center gap-1.5 px-4 py-3 rounded-xl border border-gray-300 text-gray-700 text-sm font-medium hover:bg-gray-50 disabled:opacity-50 transition-all"
            >
              <ArrowLeftIcon className="w-4 h-4" />
              上一步
            </button>
          )}
          {currentStep < 6 ? (
            <button
              onClick={goNext}
              disabled={saving}
              className="flex-1 flex items-center justify-center gap-1.5 px-4 py-3 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50 transition-all shadow-sm"
            >
              {saving ? (
                <span className="flex items-center gap-1.5">
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  保存中...
                </span>
              ) : (
                <>
                  下一步
                  <ArrowRightIcon className="w-4 h-4" />
                </>
              )}
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={saving}
              className="flex-1 flex items-center justify-center gap-1.5 px-4 py-3 rounded-xl bg-emerald-600 text-white text-sm font-semibold hover:bg-emerald-700 disabled:opacity-50 transition-all shadow-sm"
            >
              {saving ? (
                <span className="flex items-center gap-1.5">
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  提交中...
                </span>
              ) : (
                <>
                  <CheckIcon className="w-4 h-4" />
                  提交需求
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ── 外层页面（加载数据 + Provider） ──────────────────────────────────────────
export default function DetailFormPage() {
  const params = useParams();
  const formId = params?.id as string;
  const [initial, setInitial] = useState<Partial<FormData> | undefined>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!formId) return;
    fetch(`/api/detail-forms/${formId}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d) setInitial(d);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [formId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <svg className="animate-spin w-8 h-8 text-indigo-500" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p className="text-sm text-gray-500">加载表单数据...</p>
        </div>
      </div>
    );
  }

  return (
    <FormProvider initial={initial}>
      <DetailFormInner formId={formId} />
    </FormProvider>
  );
}
