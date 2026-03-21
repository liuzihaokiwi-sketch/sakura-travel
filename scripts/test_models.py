#!/usr/bin/env python3
"""
测试软规则模型是否正确导入
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from app.db.models.soft_rules import (
        EntitySoftScore,
        EditorialSeedOverride,
        SoftRuleExplanation,
        SegmentWeightPack,
        StageWeightPack,
        PreviewTriggerScore,
        SwapCandidateSoftScore,
        SoftRuleFeedbackLog,
        AreaProfile,
        TimeslotRule,
        SeasonalEvent,
        TransportLink,
        AudienceFit,
        EntityOperatingFact,
        ProductConfig,
        FeatureFlag,
        UserEvent,
    )
    
    print("✅ 所有软规则模型导入成功！")
    print(f"  1. EntitySoftScore: {EntitySoftScore.__tablename__}")
    print(f"  2. EditorialSeedOverride: {EditorialSeedOverride.__tablename__}")
    print(f"  3. SoftRuleExplanation: {SoftRuleExplanation.__tablename__}")
    print(f"  4. SegmentWeightPack: {SegmentWeightPack.__tablename__}")
    print(f"  5. StageWeightPack: {StageWeightPack.__tablename__}")
    print(f"  6. PreviewTriggerScore: {PreviewTriggerScore.__tablename__}")
    print(f"  7. SwapCandidateSoftScore: {SwapCandidateSoftScore.__tablename__}")
    print(f"  8. SoftRuleFeedbackLog: {SoftRuleFeedbackLog.__tablename__}")
    print(f"  9. AreaProfile: {AreaProfile.__tablename__}")
    print(f"  10. TimeslotRule: {TimeslotRule.__tablename__}")
    print(f"  11. SeasonalEvent: {SeasonalEvent.__tablename__}")
    print(f"  12. TransportLink: {TransportLink.__tablename__}")
    print(f"  13. AudienceFit: {AudienceFit.__tablename__}")
    print(f"  14. EntityOperatingFact: {EntityOperatingFact.__tablename__}")
    print(f"  15. ProductConfig: {ProductConfig.__tablename__}")
    print(f"  16. FeatureFlag: {FeatureFlag.__tablename__}")
    print(f"  17. UserEvent: {UserEvent.__tablename__}")
    
    # 测试 __init__.py 导入
    from app.db.models import __all__ as all_models
    print(f"\n✅ __init__.py 中包含 {len(all_models)} 个模型")
    
    # 检查软规则模型是否在 __all__ 中
    soft_rule_models = [
        "EntitySoftScore", "EditorialSeedOverride", "SoftRuleExplanation",
        "SegmentWeightPack", "StageWeightPack", "PreviewTriggerScore",
        "SwapCandidateSoftScore", "SoftRuleFeedbackLog",
        "AreaProfile", "TimeslotRule", "SeasonalEvent", "TransportLink",
        "AudienceFit", "EntityOperatingFact", "ProductConfig", "FeatureFlag", "UserEvent"
    ]
    
    missing = [model for model in soft_rule_models if model not in all_models]
    if missing:
        print(f"❌ 以下模型未在 __init__.py 中导出: {missing}")
    else:
        print("✅ 所有软规则模型已在 __init__.py 中正确导出")
        
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 其他错误: {e}")
    sys.exit(1)