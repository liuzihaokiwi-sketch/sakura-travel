#!/usr/bin/env python3
"""
测试软规则模型是否正确导入（简化版）
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 模拟 pgvector 模块
class MockVECTOR:
    pass

sys.modules['pgvector'] = type(sys)('pgvector')
sys.modules['pgvector'].sqlalchemy = type(sys)('sqlalchemy')
sys.modules['pgvector'].sqlalchemy.VECTOR = MockVECTOR

try:
    # 直接导入软规则模型
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
    
    # 检查字段定义
    print("\n✅ 检查关键字段：")
    
    # 检查 EntitySoftScore 的 12 个维度字段
    entity_fields = [col.name for col in EntitySoftScore.__table__.columns]
    print(f"  EntitySoftScore 有 {len(entity_fields)} 个字段")
    
    # 检查 12 个维度字段是否存在
    dimension_fields = [
        'emotional_value', 'shareability', 'relaxation_feel', 'memory_point',
        'localness', 'smoothness', 'food_certainty', 'night_completion',
        'recovery_friendliness', 'weather_resilience_soft',
        'professional_judgement_feel', 'preview_conversion_power'
    ]
    
    missing_dims = [dim for dim in dimension_fields if dim not in entity_fields]
    if missing_dims:
        print(f"  ❌ 缺少维度字段: {missing_dims}")
    else:
        print("  ✅ 12个维度字段完整")
    
    # 检查 ProductConfig 的 JSONB 字段
    product_fields = [col.name for col in ProductConfig.__table__.columns]
    if 'config_value' in product_fields:
        print("  ✅ ProductConfig.config_value (JSONB) 字段存在")
    
    # 检查迁移文件
    migration_path = project_root / "app" / "db" / "migrations" / "versions" / "20260321_120000_soft_rules_system_v1.py"
    if migration_path.exists():
        print(f"\n✅ 迁移文件已创建: {migration_path.name}")
        migration_size = migration_path.stat().st_size
        print(f"  文件大小: {migration_size} 字节")
    else:
        print(f"\n❌ 迁移文件不存在: {migration_path}")
        
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"❌ 其他错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)