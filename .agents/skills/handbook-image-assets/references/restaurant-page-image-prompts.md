# 餐厅页图片生成提示词

最后更新：2026-04-29

本文用于下一步通过图片接口生成餐厅手账页素材。目标不是生成整页，而是生成可以放进 `restaurant_menu_journal_v1` 的透明背景 cutout 素材。

## 一、当前页型

页型：`restaurant_menu_journal_v1`

页面只做单家餐厅，不做照片卡拼贴。结构为：

1. 右上角店名区。
2. 第一块：餐厅整体介绍，配主食物插图。
3. 第二块：推荐菜品，配第二张食物插图。
4. 第三块：到店体验，配店面插图。

## 二、需要生成的三张图

建议输出到：

```text
japan/kansai/assets/routes/osaka/osakajo_namba/generated/restaurant/
```

并同步优化到：

```text
web/public/handbook-assets/osaka/osakajo-namba/restaurant/generated/
```

### 1. 主食物 cutout

文件名建议：

```text
restaurant_food_primary_cutout.png
```

用途：第一块“餐厅整体介绍”的大食物插图。

提示词：

```text
Create a transparent-background watercolor cutout illustration of the restaurant's main food.

The food should feel hand-drawn for a travel journal restaurant page, not like a photo. Keep the food recognizable and appetizing. Use loose ink lines, soft watercolor texture, warm colors, and natural imperfect edges.

Composition:
- One main food group only
- No plate frame unless the food naturally needs a plate
- No table background
- No menu page, no notebook, no photo card
- Transparent background
- Slightly irregular watercolor edge
- Leave no hard rectangular white background

Style:
refined travel journal sketch, handmade watercolor, light ink, warm and casual, printable.

No text, no labels, no logo, no watermark, no speech bubble, no frame, no sticker outline.
```

### 2. 推荐菜品 cutout

文件名建议：

```text
restaurant_food_secondary_cutout.png
```

用途：第二块“推荐菜品”的辅助食物插图。

提示词：

```text
Create a small transparent-background watercolor cutout illustration of a recommended dish for the same restaurant page.

The image should be smaller and simpler than the main food illustration. It should work as a supporting hand-drawn food element placed beside short handwritten notes.

Composition:
- One secondary dish only
- Clear silhouette at small size
- Transparent background
- Soft irregular watercolor edge
- No rectangular white background
- No photo-card border

Style:
same travel journal watercolor and ink style as the main food image.

No text, no labels, no logo, no watermark, no menu layout, no notebook mockup.
```

### 3. 店面 cutout / 不规则边缘小图

文件名建议：

```text
restaurant_storefront_cutout.png
```

用途：第三块“到店体验”的店面插图。

提示词：

```text
Create a transparent-background watercolor cutout illustration of the restaurant storefront.

Use the reference storefront photo to keep the shop identity, entrance shape, lanterns/signage shapes, doorway, and street feeling recognizable. This is a supporting illustration for a restaurant travel journal page, not a full street scene.

Composition:
- Show the storefront or entrance as the main subject
- Keep it compact enough to sit in the lower part of a narrow journal page
- Transparent background outside the storefront
- Irregular watercolor cutout edge is allowed
- Do not make it a rectangular photo
- Do not include a notebook page or page mockup
- Avoid readable fake text; signage can be simplified as shapes

Style:
hand-drawn watercolor storefront, light ink lines, warm evening restaurant feeling, handmade travel journal aesthetic.

No route map, no people crowd blocking the entrance, no readable fake text, no logo, no watermark, no photo frame.
```

## 三、渲染接入口径

当前前端原型位于：

```text
web/app/render/osakajo-namba-scrapbook/page.tsx
```

当前使用 `raw` 图片作为 fallback。生成透明 PNG 后，将页面顶部 `assets` 替换为：

```ts
const assets = {
  foodA: "/handbook-assets/osaka/osakajo-namba/restaurant/generated/restaurant_food_primary_cutout.png",
  foodB: "/handbook-assets/osaka/osakajo-namba/restaurant/generated/restaurant_food_secondary_cutout.png",
  shop: "/handbook-assets/osaka/osakajo-namba/restaurant/generated/restaurant_storefront_cutout.png",
};
```

原则：

- 餐厅页只读成品透明素材。
- 不在前端裁大图来伪装透明素材。
- 不让图片模型生成整张餐厅页。
- 不让图片模型生成中文正文，文字由前端排版。
