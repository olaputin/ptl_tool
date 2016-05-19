
% include('header.tpl')

<div class="row">
    <div class="col-md-1"></div>
<div class="col-md-2">
    <a onclick="ptl_request('checkout')"
       class="btn btn-info operation_button has-spinner {{'disabled' if status['checkout'] else '' }}"
       id="checkout_btn">
        <span class="spinner"><i class="fa fa-spinner fa-pulse"></i></span>
        Checkout
    </a></br>
    <h5>{{last_exec['checkout']}}</h5>
</div>
<div class="col-md-2">
    <a onclick="ptl_request('save')"
       class="btn btn-success operation_button has-spinner {{'disabled' if status['save'] else '' }}"
       id="save_btn">
        <span class="spinner"><i class="fa fa-spinner fa-pulse"></i></span>
        Save
    </a></br>
    <h5>{{ last_exec['save'] }}</h5>
</div>
<div class="col-md-2">
    <a onclick="ptl_request('commit')"
       class="btn btn-danger operation_button has-spinner {{'disabled' if status['commit'] else '' }}"
       type="submit"
       id="commit_btn">
        <span class="spinner"><i class="fa fa-spinner fa-pulse"></i></span>
        Commit
    </a><br>
    <h5>{{ last_exec['commit'] }}</h5>
</div>
</div>