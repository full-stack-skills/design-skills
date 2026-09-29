"use strict";
// 仅供同源评审器使用。只传页面身份与显示选项，不传表单、凭据或写入操作。
window.readPreviewView = function () {
  let page = state.page;
  if (state.drawer) page = 'drawer';
  else if (page === 'chat' && state.conversation) page = 'conversation';
  else if (page === 'settings') {
    if (importDraft) page = importDraft.kind + '-import';
    else if (!settingsDetail) page = 'settings';
    else if (state.settingsTab !== 'model') page = state.settingsTab;
    else if (providerPicker) page = 'model-providers';
    else if (modelDialog === 'fetch') page = 'model-fetch';
    else if (modelScreen === 'edit') page = modelConnections.some(c => c.id === modelDraft?.id) ? 'model-detail' : 'model-editor';
    else page = 'model';
  }
  // 未保存决定留在操作端；不能替另一端作出保存/放弃决定。
  if (modelDialog === 'leave') return null;
  return {
    page, theme: state.theme,
    importMode: importDraft?.mode === 'archive' ? 'archive' : 'link',
    connection: modelConnections.some(c => c.id === modelDraft?.id) ? modelDraft.id : null,
    provider: modelDraft?.provider || null,
    modelOverlay: modelDialog === 'manual' ? 'manual' : null,
    modelIndex: modelDialog === 'manual' ? modelEditIndex : -1,
    category: state.category, scope: state.scope, taskTab: state.taskTab,
    item: state.selectedItem,
    modal: ['schedule','permission','login-expired','add'].includes(state.modal) ? state.modal : null,
    productModal: ['model','document'].includes(productModal) ? productModal : null,
    configEditor: editorKind ? editorKind.kind : null
  };
};
window.applyPreviewView = function (view) {
  const current = window.readPreviewView();
  if (Object.values(catalog).flat().some(item => item.id === view.item)) state.selectedItem = view.item;
  // 同一导入弹窗换方式时保留接收端自己的输入；不会复制另一端的链接/文件。
  if (importDraft && current?.page === view.page) {
    captureImport();
    importDraft.mode = view.importMode === 'archive' ? 'archive' : 'link';
    importDraft.step = 'source';
    importDraft.error = '';
  } else {
    window.previewRoute(view.page);
    if (importDraft) importDraft.mode = view.importMode === 'archive' ? 'archive' : 'link';
  }
  if (['model-detail','model-fetch','model-editor'].includes(view.page)) {
    const connection = modelConnections.find(c => c.id === view.connection);
    if (connection) { modelDraft = structuredClone(connection); modelScreen = 'edit'; }
    else if (view.page === 'model-editor' && modelProviders.some(p => p.id === view.provider)) modelPick(view.provider);
    if (view.modelOverlay === 'manual') {
      modelDialog = 'manual';
      modelEditIndex = Number.isInteger(view.modelIndex) && view.modelIndex >= 0 && view.modelIndex < modelDraft.models.length ? view.modelIndex : -1;
    }
  }
  if (Object.hasOwn(categoryNames, view.category)) state.category = view.category;
  if (['discover','installed'].includes(view.scope)) state.scope = view.scope;
  if (['running','schedule','done'].includes(view.taskTab)) state.taskTab = view.taskTab;
  if (settingsItems().some(item => item[0] === view.configEditor)) editorKind = {kind: view.configEditor};
  state.modal = ['schedule','permission','login-expired'].includes(view.modal) || (view.modal === 'add' && findItem()) ? view.modal : null;
  productModal = ['model','document'].includes(view.productModal) ? view.productModal : null;
  state.theme = view.theme === 'dark' ? 'dark' : 'light';
  render();
};
const previewNavigationActions = new Set([
  'open-item','open-search-item','pad-open','add-item','create-task','close-modal','permission','login-expired','model','view-knowledge','product-close',
  'drawer','new-chat','open-history','search','z-category','z-back','z-import','z-new','z-edit','z-editor-close',
  'imp-mode','imp-close','imp-back','mc-edit','mc-exit','mc-list','mc-add','mc-picker-close','mc-pick',
  'mc-fetch','mc-model-add','mc-model-edit','mc-dialog-close'
]);
// 在应用事件处理器之后注册，读取最终视图。程序化回放不产生点击事件。
document.addEventListener('click', event => {
  const action = event.target.closest('[data-action]')?.dataset.action;
  if (!action || !(previewNavigationActions.has(action) || /^(go-|theme-|category-|scope-|task-)/.test(action))) return;
  queueMicrotask(() => window.onPreviewChange?.(window.readPreviewView()));
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape') queueMicrotask(() => window.onPreviewChange?.(window.readPreviewView()));
});
