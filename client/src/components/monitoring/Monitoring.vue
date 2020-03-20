<template>
  <div>
    <v-layout style="margin-left:8px; margin-right:8px;">
      <v-flex xs3 v-for="item in links" :key="item.id" style="margin:5px;">
        <v-hover>
          <v-card slot-scope="{ hover }" :class="`elevation-${hover ? 12 : 2}`">
            <v-img height="10px" :class="item.color"></v-img>
            <v-card-title primary-title style="padding-bottom:10px;">
              <p class="text-xs-center" style="margin-bottom:0px;">
                <span class="title">{{item.title}}</span>
                <br>
                <span class="body-2">{{item.region}}</span>
              </p>
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text style="padding-bottom:1px;">
              <p class="font-weight-medium">Hostname<pre>127.0.0.1</pre></p>
              <p class="font-weight-medium">Connections<pre>23</pre></p>
            </v-card-text>
          </v-card>
        </v-hover>
      </v-flex>      
    </v-layout>
  </div>
</template>

<script>
  export default {
    data() {
      return {
        links: [
          { id: '1', title: 'Templates EU', region: 'AWS-EU', color: 'teal' },
          { id: '2', title: 'Templates US', region: 'AWS-US', color: 'red' },
          { id: '3', title: 'Templates JP', region: 'AWS-JP', color: 'orange' },
          { id: '4', title: 'Aurora Apps', region: 'AWS-EU', color: 'teal' }      
        ]
      }
    }
  }
</script>