const KEY_CODE_ESCAPE = 27;

const LOCAL_STORAGE = window.localStorage;
const LOCAL_STORAGE_KEY_SHOW_CATEGORIES = 'LOCAL_STORAGE_KEY_SHOW_CATEGORIES';

const ENDPOINT_UPDATE_VIDEO_ITEM = '/update-video-item';
const ENDPOINT_IGNORE_CHANNEL = '/ignore-channel';

const ENDPOINT_ADD_CHANNEL_TARGET = '/add-channel-target';
const VIDEO_STATUS_ID_APPROVED = 2;
const VIDEO_STATUS_ID_IGNORED = 3;

const $document = $(document);
const $body = $('body');
const $showAllCategoriesCheckbox = $('#show-all-categories-checkbox');

const $channelDetailsPopups = $('.channel-details-popup-wr');

let $pageFilteringFormInitState = null;
let $activeChannelDetailsPopup = null;

function activateChannelDetailsPopup ($elem) {
    $activeChannelDetailsPopup = $elem;
    $elem.removeClass('d-none');
}

function deactivateChannelDetailsPopup () {
    if ($activeChannelDetailsPopup) {
        $activeChannelDetailsPopup.addClass('d-none');

        $activeChannelDetailsPopup = null;
    }
}

function init () {
    $pageFilteringFormInitState =  $('.page-filtering-params-form').clone(false);
    $pageFilteringFormInitState.addClass('d-none');
    $body.append($pageFilteringFormInitState);

    //channel details popup setup
    
    $('.channel-details-btn').on('click', function () {
        const $popup = $(this).parent().find('.channel-details-popup-wr');

        setTimeout(function () {
            activateChannelDetailsPopup($popup);
        }, 10);
    });

    $(window).click(deactivateChannelDetailsPopup);
    
    $channelDetailsPopups.on('click', function(event){
        event.stopPropagation();
    });

    $('.add-channel-target-btn').on('click', function (e) {
        e.preventDefault();
        e.stopPropagation();

        const videoItemId = parseInt($(this).attr('data-video-item-id'));
        const $videoBlock = $('#video-' + videoItemId);

        const channelId = $(this).attr('data-channel-id');
        const channelName = $(this).attr('data-channel-name');
        const providerId = parseInt($(this).attr('data-provider-id'));
        const videoTypeId = parseInt($(this).attr('data-video-type-id'));

        if (confirm('add channel target ' + channelId + '?')) {
            addChannelTarget(videoItemId, channelId, channelName, providerId, videoTypeId, $videoBlock);
        };
    });

    $('.ignore-channel-btn').on('click', function (e) {
        e.preventDefault();
        e.stopPropagation();

        const videoItemId = parseInt($(this).attr('data-video-item-id'));
        const $videoBlock = $('#video-' + videoItemId);

        const channelId = $(this).attr('data-channel-id');
        const providerId = parseInt($(this).attr('data-provider-id'));

        if (confirm('completely ignore channel ' + channelId + '?')) {
            ignoreChannel(videoItemId, channelId, providerId, $videoBlock);
        };
    });

    $('.video-preview-img').on('click', function () {
        const videoItemId = parseInt($(this).attr('data-video-item-id'));

        replacePreviewImgWithVideoEmbedWr(videoItemId);
    });

    $('.toggle-video-embed-enlarge-vertical, .toggle-video-embed-enlarge-horizontal').on('click', function () {
        const videoItemId = parseInt($(this).attr('data-video-item-id'));
        const aspect = $(this).attr('data-aspect');

        replacePreviewImgWithVideoEmbedWr(videoItemId);
        
        toggleVideoEmbedEnlarge(videoItemId, aspect);
    });

    $('.toggle-video-embed-close-video').on('click', function () {
        const videoItemId = parseInt($(this).attr('data-video-item-id'));

        replaceVideoEmbedWrWithPreviewImg(videoItemId);
    });

    $document.on('keydown', function(e) {
        if (e.which === KEY_CODE_ESCAPE) {
            $('.video-embed-wr-enlarge-vertical, .video-embed-wr-enlarge-horizontal').each(function () {
                const videoItemId = parseInt($(this).attr('data-video-item-id'));

                toggleVideoEmbedEnlarge(videoItemId, '', true);
            });

            deactivateChannelDetailsPopup();
        }
    });

    $('.pagination-btn').on('click', function () {
        const btn = $(this);

        $pageFilteringFormInitState.find('.pagination-value-input').val(btn.attr('data-page-num'));
        $pageFilteringFormInitState.submit();
    });

    const showCategories = LOCAL_STORAGE.getItem(LOCAL_STORAGE_KEY_SHOW_CATEGORIES) === 'true';

    if (showCategories) {
        $('.collapse').collapse('show');
        $showAllCategoriesCheckbox.attr('checked', true);
    }
    
    $showAllCategoriesCheckbox.on('click', function () {
        if ($showAllCategoriesCheckbox.is(':checked')) {
            $('.collapse').collapse('show');
            LOCAL_STORAGE.setItem(LOCAL_STORAGE_KEY_SHOW_CATEGORIES, true);
        } else {
            $('.collapse').collapse('hide');
            LOCAL_STORAGE.setItem(LOCAL_STORAGE_KEY_SHOW_CATEGORIES, false);
        }
    });

    $('.uploaded-time-clear').on('click', function () {
        const videoItemId = parseInt($(this).attr('data-video-item-id'));
        const $videoBlock = $('#video-' + videoItemId);
        
        const $uploadTimeClearCheckbox = $videoBlock.find('.uploaded-time-clear-checkbox');
        $uploadTimeClearCheckbox.removeClass('d-none');
        $uploadTimeClearCheckbox.prop('checked', true);
    });

    $('.video-ignore-btn').on('click', function () {
        const videoItemId = parseInt($(this).attr('data-video-item-id'));
        const $videoBlock = $('#video-' + videoItemId);

        updateVideoInfo(videoItemId, $videoBlock, VIDEO_STATUS_ID_IGNORED);
    });
    $('.video-update-btn').on('click', function () {
        const videoItemId = parseInt($(this).attr('data-video-item-id'));
        const $videoBlock = $('#video-' + videoItemId);

        updateVideoInfo(videoItemId, $videoBlock, null);
    });
    $('.video-approve-btn').on('click', function () {
        const videoItemId = parseInt($(this).attr('data-video-item-id'));
        const $videoBlock = $('#video-' + videoItemId);

        updateVideoInfo(videoItemId, $videoBlock, VIDEO_STATUS_ID_APPROVED);
    });
}

function updateVideoInfo (videoItemId, $videoBlock, forceStatus) {
    const $titleInput = $videoBlock.find('.video-title-input');
    const $videoStatusIdSelect = $videoBlock.find('.video-item-status');
    const $editorPickSetCheckbox = $videoBlock.find('.video-editor-pick');
    const $uploadTimeClearCheckbox = $videoBlock.find('.uploaded-time-clear-checkbox');
    const $videoCategoryIdCheckboxes = $videoBlock.find('.video-category-input');

    const $inputBlocks = $([
        $titleInput,
        $videoStatusIdSelect,
        $editorPickSetCheckbox,
        $uploadTimeClearCheckbox,
        $videoCategoryIdCheckboxes,
    ]);

    $inputBlocks.each(function () {
        $(this).attr('disabled', true);
    });

    const $categoriesCollapsibleWr = $('#video-categories-collapsable-' + videoItemId);

    if (forceStatus) {
        $videoStatusIdSelect.val(forceStatus).change();
    }

    const newTitle = $titleInput.val();
    const newVideoStatusId = parseInt($videoStatusIdSelect.find(":selected").val());
    const newEditorPickSet = $editorPickSetCheckbox.is(':checked');
    const uploadTimeClearSet = $uploadTimeClearCheckbox.is(':checked');

    const newVideoCategoryIdsArr = [];
    $videoCategoryIdCheckboxes.each(function () {
        const $checkbox = $(this);
        if ($checkbox.is(':checked')) {
            newVideoCategoryIdsArr.push(parseInt($checkbox.attr('name')));
        }
    });

    const updateParams = {
        video_item_id: videoItemId,
        new_title: newTitle,
        new_video_status_id: newVideoStatusId,
        new_editor_pick_set: newEditorPickSet,
        upload_time_clear_set: uploadTimeClearSet,
        new_video_category_ids: newVideoCategoryIdsArr
    };

    $.ajax({
        url: ENDPOINT_UPDATE_VIDEO_ITEM,
        type: "POST",
        data: JSON.stringify(updateParams),
        processData: false,
        contentType: "application/json; charset=UTF-8",
        success: function (data, textStatus, jqXHR) {
            $inputBlocks.each(function () {
                $(this).removeAttr('disabled', true);
            });

            if (!$showAllCategoriesCheckbox.is(':checked')) {
                $categoriesCollapsibleWr.collapse('hide');
            }

            if (uploadTimeClearSet) {
                $videoBlock.find('.video-date-uploaded-wr').text('not uploaded');
            }

            $videoBlock.css('box-shadow', '0px 0px 8px 3px rgb(68 161 19 / 80%)');

            if (parseInt($videoBlock.attr('data-initial-status_id')) != newVideoStatusId) {
                $videoStatusIdSelect.css('box-shadow', '0px 0px 4px 2px rgb(68 161 19 / 80%)');
            }

            replaceVideoEmbedWrWithPreviewImg(videoItemId);
        },
        error: function (jqXHR, textStatus, errorThrown) {
            $videoBlock.css('box-shadow', '0px 0px 2px 3px rgb(161 19 19 / 80%)');
 
            $inputBlocks.each(function () {
                $(this).removeAttr('disabled', true);
            });

            replaceVideoEmbedWrWithPreviewImg(videoItemId);
            
            alert('Error updading video item ' + videoItemId + ', status: ' + textStatus + ', message: ' + errorThrown);
        }
    });
}

function addChannelTarget (videoItemId, channelId, channelName, providerId, videoTypeId, $videoBlock) {
    const data = {
        channel_id: channelId,
        channel_name: channelName,
        provider_id: providerId,
        video_type_id: videoTypeId
    };

    $.ajax({
        url: ENDPOINT_ADD_CHANNEL_TARGET,
        type: "POST",
        data: JSON.stringify(data),
        processData: false,
        contentType: "application/json; charset=UTF-8",
        success: function (data, textStatus, jqXHR) {
            if (data && data.status == 'ok') {
                const msg = 'added channel target for "' + channelId + '". ' + data.message;
                //alert(msg);
                console.log(msg);

                deactivateChannelDetailsPopup();

                replaceVideoEmbedWrWithPreviewImg(videoItemId);

                $videoBlock.css('box-shadow', '0px 0px 8px 3px rgb(68 161 19 / 80%)');
            } else {
                replaceVideoEmbedWrWithPreviewImg(videoItemId);

                alert('got error: ' + data ? data.message : '... no data obj ...');
            }
        },
        error: function (jqXHR, textStatus, errorThrown) {
            alert('error! ' + textStatus + ' / ' + errorThrown);
        }
    });
}

function ignoreChannel (videoItemId, channelId, providerId, $videoBlock) {
    const data = {
        channel_id: channelId,
        provider_id: providerId
    };

    $.ajax({
        url: ENDPOINT_IGNORE_CHANNEL,
        type: "POST",
        data: JSON.stringify(data),
        processData: false,
        contentType: "application/json; charset=UTF-8",
        success: function (data, textStatus, jqXHR) {
            if (data && data.status == 'ok') {
                const msg = 'ignored channel "' + channelId + '". ' + data.message;
                //alert(msg);
                console.log(msg);

                deactivateChannelDetailsPopup();

                replaceVideoEmbedWrWithPreviewImg(videoItemId);

                $videoBlock.css('box-shadow', '0px 0px 4px 2px rgb(0 0 0 / 100%)');
            } else {
                replaceVideoEmbedWrWithPreviewImg(videoItemId);

                alert('got error: ' + data ? data.message : '... no data obj ...');
            }
        },
        error: function (jqXHR, textStatus, errorThrown) {
            alert('error! ' + textStatus + ' / ' + errorThrown);
        }
    });
}

function replacePreviewImgWithVideoEmbedWr (videoItemId) {
    const $videoBlock = $('#video-' + videoItemId);

    const $vidImg = $videoBlock.find('.video-preview-img');
    const $vidEmbedWr = $videoBlock.find('.video-embed-wr');

    if ($vidEmbedWr.hasClass('d-none')) {
        //video is embedded through html insertion 
        if ($vidEmbedWr.hasClass('insert-html-wr')) {
            const htmlAsString = $vidEmbedWr.attr('data-embed-block-html');
            $vidEmbedWr.html(htmlAsString);
        } else {
            $vidEmbedWr.attr('src', $vidEmbedWr.attr('data-src'));
        }
       
        $vidEmbedWr.removeClass('d-none');
        $vidImg.addClass('d-none');
    }
}

function replaceVideoEmbedWrWithPreviewImg (videoItemId) {
    const $videoBlock = $('#video-' + videoItemId);

    const $vidImg = $videoBlock.find('.video-preview-img');
    const $vidEmbedWr = $videoBlock.find('.video-embed-wr');

    toggleVideoEmbedEnlarge(videoItemId, '', true);

    if ($vidImg.hasClass('d-none')) {
        //video is embedded through html insertion 
        if ($vidEmbedWr.hasClass('insert-html-wr')) {
            $vidEmbedWr.html('');
        } else {
            $vidEmbedWr.attr('src', '');
        }
       
        $vidEmbedWr.addClass('d-none');
        $vidImg.removeClass('d-none');
    }
}

function toggleVideoEmbedEnlarge (videoItemId, enlargeAspect, forceRemove) {
    const $videoBlock = $('#video-' + videoItemId);
    const $vidEmbedWr = $videoBlock.find('.video-embed-wr');
    const $vidImg = $videoBlock.find('.video-preview-img');
    
    if (forceRemove || $vidEmbedWr.attr('data-is-enlarged') == 'true') {
        $vidEmbedWr.attr('data-is-enlarged', 'false');

        $vidEmbedWr.removeClass('video-embed-wr-enlarge-vertical');
        $vidEmbedWr.removeClass('video-embed-wr-enlarge-horizontal');

        if (!$vidEmbedWr.hasClass('d-none')) {
            $vidImg.addClass('d-none');
        }
    } else {
        $vidEmbedWr.attr('data-is-enlarged', 'true');

        $vidEmbedWr.addClass('video-embed-wr-enlarge-' + enlargeAspect);
        $vidImg.removeClass('d-none');
    }
}